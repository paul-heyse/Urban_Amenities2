import gzip
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, Polygon

from Urban_Amenities2.config.loader import load_params
from Urban_Amenities2.dedupe.pois import DedupeConfig, deduplicate_pois
from Urban_Amenities2.io.airports.faa import compute_weights, index_airports
from Urban_Amenities2.io.climate.noaa import NOAAConfig, NoaaNormalsIngestor
from Urban_Amenities2.io.education.childcare import combine_registries
from Urban_Amenities2.io.education.ipeds import compute_weights as ipeds_weights
from Urban_Amenities2.io.education.nces import prepare_schools
from Urban_Amenities2.io.enrichment import merge_enrichment
from Urban_Amenities2.io.enrichment.wikidata import WikidataEnricher
from Urban_Amenities2.io.enrichment.wikipedia import compute_statistics
from Urban_Amenities2.io.gtfs.realtime import GTFSRealtimeIngestor
from Urban_Amenities2.io.gtfs.registry import load_registry
from Urban_Amenities2.io.gtfs.static import GTFSCache, GTFSStaticIngestor
from Urban_Amenities2.io.jobs.lodes import LODESConfig, LODESIngestor
from Urban_Amenities2.io.overture.transportation import prepare_transportation
from Urban_Amenities2.io.parks.padus import index_to_hex
from Urban_Amenities2.io.parks.ridb import RIDBIngestor
from Urban_Amenities2.io.parks.trails import index_trails
from Urban_Amenities2.io.quality.checks import coverage_check
from Urban_Amenities2.io.versioning.snapshots import SnapshotRegistry
from Urban_Amenities2.quality import (
    BrandDedupeConfig,
    QualityScorer,
    build_scoring_config,
    summarize_quality,
)
from Urban_Amenities2.xwalk.overture_aucs import load_crosswalk


def test_crosswalk_and_dedupe(tmp_path: Path) -> None:
    matcher = load_crosswalk()
    sample = pd.DataFrame(
        {
            "poi_id": ["1", "2"],
            "primary_category": ["eat_and_drink.restaurant.italian_restaurant", "eat_and_drink.fast_food"],
            "alternate_categories": [[], []],
            "operating_status": ["open", "open"],
            "lat": [39.0, 39.0],
            "lon": [-104.0, -104.0],
            "name": ["Luigi", "Burger"],
            "brand": ["", ""],
            "confidence": [0.9, 0.8],
        }
    )
    assigned = matcher.assign(sample)
    assert assigned.loc[0, "aucstype"] == "restaurants_full_service"
    assert assigned.loc[1, "aucstype"] == "fast_food_quick"

    deduped = deduplicate_pois(
        assigned.assign(hex_id="abc", quality=1.0),
        config=DedupeConfig(brand_distance_m=10.0, name_distance_m=10.0),
    )
    assert len(deduped) == 2

    network = pd.DataFrame(
        {
            "class": ["road"],
            "geometry": [LineString([(0, 0), (1, 1)])],
            "speed_limits": [[{"unit": "kmh", "value": 50}]],
            "access_restrictions": [[]],
            "connectors": [[]],
        }
    )
    prepared = prepare_transportation(network)
    assert prepared.loc[0, "mode_car"]
    assert prepared.loc[0, "mode_foot"]
    assert prepared.loc[0, "mode_bike"]


def _create_gtfs_zip(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr(
            "stops.txt",
            "stop_id,stop_name,stop_lat,stop_lon\nS1,Stop 1,39.0,-104.0\nS2,Stop 2,39.1,-104.1\n",
        )
        zf.writestr(
            "routes.txt",
            "route_id,agency_id,route_short_name,route_type\nR1,1,1,3\n",
        )
        zf.writestr(
            "trips.txt",
            "route_id,service_id,trip_id\nR1,WD,T1\n",
        )
        zf.writestr(
            "stop_times.txt",
            "trip_id,arrival_time,departure_time,stop_id,stop_sequence\nT1,08:00:00,08:00:00,S1,1\nT1,08:10:00,08:10:00,S2,2\n",
        )
        zf.writestr(
            "calendar.txt",
            "service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\nWD,1,1,1,1,1,0,0,20240101,20241231\n",
        )
def test_gtfs_pipeline(tmp_path: Path) -> None:
    registry = load_registry()
    assert any(agency.name.startswith("RTD") for agency in registry)

    gtfs_zip = tmp_path / "feed.zip"
    _create_gtfs_zip(gtfs_zip)
    static = GTFSStaticIngestor(cache=GTFSCache(directory=tmp_path / "cache"), registry=SnapshotRegistry(tmp_path / "snap.jsonl"))
    agency = registry[0]
    agency.static_url = gtfs_zip.as_uri()
    outputs = static.ingest(agency, output_dir=tmp_path)
    assert (tmp_path / "gtfs_headways.parquet").exists()
    assert {"stops", "routes", "headways"}.issubset(outputs.keys())

    # realtime stub
    from gtfs_realtime_bindings import feedmessage_pb2

    feed = feedmessage_pb2.FeedMessage()
    entity = feed.entity.add()
    entity.id = "1"
    entity.trip_update.trip.trip_id = "T1"
    entity.trip_update.trip.route_id = "R1"
    stu = entity.trip_update.stop_time_update.add()
    stu.stop_sequence = 1
    stu.departure.delay = 60
    feed_path = tmp_path / "realtime.pb"
    feed_path.write_bytes(feed.SerializeToString())
    agency.realtime_urls = [feed_path.as_uri()]
    realtime = GTFSRealtimeIngestor(registry=SnapshotRegistry(tmp_path / "snap.jsonl"))
    output = realtime.ingest(agency, output_path=tmp_path / "realtime.parquet")
    metrics = pd.read_parquet(output)
    assert "avg_delay_sec" in metrics.columns


def test_climate_and_parks(tmp_path: Path) -> None:
    payload = {
        "results": [
            {
                "station": "ST1",
                "month": "1",
                "latitude": 39.0,
                "longitude": -104.0,
                "MLY-TAVG-NORMAL": 12,
                "MLY-PRCP-PRB": 20,
                "MLY-WSF2-NORMAL": 3,
            }
        ]
    }
    ingest = NoaaNormalsIngestor(NOAAConfig())
    frame = ingest._normalise_columns(pd.DataFrame(payload["results"]))
    frame["hex_id"] = "abc"
    comfort = ingest.compute_comfort_index(frame)
    assert 0 <= comfort.loc[0, "sigma_out"] <= 1

    padus = gpd.GeoDataFrame(
        {"Access": ["Open"], "State": ["CO"], "Unit_Name": ["Park"], "geometry": [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])]},
        crs="EPSG:4326",
    )
    parks = index_to_hex(padus)
    assert "hex_id" in parks.columns

    trails = gpd.GeoDataFrame({"geometry": [LineString([(0, 0), (1, 1)])]})
    trails_hex = index_trails(trails, samples=3)
    assert not trails_hex.empty

    ridb = RIDBIngestor(registry=SnapshotRegistry(tmp_path / "snap.jsonl"))
    recareas = pd.DataFrame(
        {"recarea_id": [1], "name": ["Area"], "lat": [39.0], "lon": [-104.0], "states": ["CO"]}
    )
    indexed_recreation = ridb.index_to_hex(recareas)
    assert "hex_id" in indexed_recreation.columns


def test_jobs_and_education(tmp_path: Path) -> None:
    lodes_csv = tmp_path / "co_wac.csv.gz"
    data = "w_geocode,C000,CNS01\n123450000001,10,10\n"
    lodes_csv.write_bytes(gzip.compress(data.encode("utf-8")))
    config = LODESConfig(states=["co"])
    ingestor = LODESIngestor(config, registry=SnapshotRegistry(tmp_path / "snap.jsonl"))
    frame = ingestor.fetch_state("co")
    geocodes = pd.DataFrame({"block_geoid": ["123450000001"], "lat": [39.0], "lon": [-104.0]})
    geocoded = ingestor.geocode_blocks(frame, geocodes)
    allocated = ingestor.allocate_to_hex(geocoded)
    assert "hex_id" in allocated.columns

    public = pd.DataFrame({"NCESSCH": ["1"], "SCH_NAME": ["School"], "LAT": [39.0], "LON": [-104.0], "LEVEL": ["High"], "ENR_TOTAL": [100], "TOTFTE": [10]})
    private = pd.DataFrame({"NCESSCH": ["2"], "SCH_NAME": ["Private"], "LAT": [39.1], "LON": [-104.1], "LEVEL": ["High"], "ENR_TOTAL": [50], "TOTFTE": [5]})
    schools = prepare_schools(public, private)
    assert set(schools["hex_id"])  # hex IDs assigned

    directory = pd.DataFrame({"unitid": [1], "latitude": [39.0], "longitude": [-104.0]})
    carnegie = pd.DataFrame({"unitid": [1], "carnegie": ["R1"]})
    universities = ipeds_weights(directory.merge(carnegie, on="unitid"))
    assert "q_u" in universities.columns

    registries = {"CO": pd.DataFrame({"provider_id": [1], "name": ["Care"], "lat": [39.0], "lon": [-104.0], "capacity": [20]})}
    childcare = combine_registries(registries)
    assert "hex_id" in childcare.columns

    airports = pd.DataFrame({"LAT": [39.0], "LON": [-104.0], "ENPLANEMENTS": [1000]})
    indexed = index_airports(compute_weights(airports))
    assert "weight" in indexed.columns


def test_enrichment_and_quality(tmp_path: Path) -> None:
    class StubClient:
        def query(self, query: str) -> dict:
            return {"results": {"bindings": [{"item": {"value": "http://www.wikidata.org/entity/Q1"}, "capacity": {"value": "500"}}]}}

    pois = pd.DataFrame(
        {
            "poi_id": ["A", "B"],
            "name": ["Museum", "Museum Annex"],
            "lat": [39.0, 39.002],
            "lon": [-104.0, -104.002],
            "aucstype": ["museum", "museum"],
            "brand": ["National Museum", "National Museum"],
            "hours_per_day": [10, 24],
        }
    )
    wikidata = WikidataEnricher(StubClient()).enrich(pois)
    wiki_stats = compute_statistics({"A": pd.DataFrame({"pageviews": [10, 20, 30]})})
    wiki_stats = wiki_stats.assign(poi_id=wiki_stats["title"]).drop(columns=["title"])
    params, _ = load_params("configs/params_default.yml")
    scorer = QualityScorer(build_scoring_config(params.quality))
    dedupe_config = BrandDedupeConfig(beta_per_km=params.quality.dedupe_beta_per_km)
    enriched = merge_enrichment(
        pois,
        wikidata,
        wiki_stats,
        quality_scorer=scorer,
        brand_dedupe_config=dedupe_config,
    )
    assert "quality_attrs" in enriched.columns
    assert "quality" in enriched.columns
    assert enriched["quality"].between(0, 100).all()
    assert "brand_penalty" in enriched.columns
    assert enriched.loc[enriched["poi_id"] == "B", "brand_penalty"].iloc[0] < 1.0

    quality = coverage_check(enriched.assign(hex_id="abc"))
    assert quality["hex_count"] == 1

    summary = summarize_quality(enriched, category_col="aucstype")
    assert not summary.empty
    assert summary.loc[0, "mean_quality"] >= 0


