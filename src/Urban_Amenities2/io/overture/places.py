from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from ...dedupe.pois import DedupeConfig, deduplicate_pois
from ...hex.aggregation import points_to_hex
from ...logging_utils import get_logger
from ...xwalk.overture_aucs import CategoryMatcher, load_crosswalk

LOGGER = get_logger("aucs.ingest.overture")


BBox = Tuple[float, float, float, float]


@dataclass
class BigQueryConfig:
    project: str
    dataset: str
    table: str = "places"

    def table_ref(self) -> str:
        return f"`{self.project}.{self.dataset}.{self.table}`"


def build_bigquery_query(config: BigQueryConfig, state: Optional[str] = None, bbox: BBox | None = None) -> str:
    where: list[str] = ["operating_status = 'open'"]
    if state:
        where.append("address_components.administrative_area = @state")
    if bbox:
        min_lon, min_lat, max_lon, max_lat = bbox
        where.append("ST_CONTAINS(ST_GEOGFROMTEXT(@bbox), geometry)")
    where_clause = " AND ".join(where)
    select_columns = [
        "id",
        "display.name AS name",
        "categories.primary AS primary_category",
        "categories.alternate AS alternate_categories",
        "brand",
        "confidence",
        "geometry.latitude AS lat",
        "geometry.longitude AS lon",
        "opening_hours",
        "operating_status",
    ]
    query = f"SELECT {', '.join(select_columns)} FROM {config.table_ref()} WHERE {where_clause}"
    return query


def read_places_from_bigquery(
    config: BigQueryConfig,
    client=None,
    state: Optional[str] = None,
    bbox: BBox | None = None,
) -> pd.DataFrame:
    from google.cloud import bigquery  # type: ignore

    if client is None:
        client = bigquery.Client(project=config.project)
    job_config = bigquery.QueryJobConfig()
    if state:
        job_config.query_parameters.append(bigquery.ScalarQueryParameter("state", "STRING", state))
    if bbox:
        polygon = _bbox_to_wkt(bbox)
        job_config.query_parameters.append(bigquery.ScalarQueryParameter("bbox", "STRING", polygon))
    query = build_bigquery_query(config, state=state, bbox=bbox)
    LOGGER.info("querying_overture_bigquery", query=query)
    result = client.query(query, job_config=job_config)
    return result.result().to_dataframe(create_bqstorage_client=False)


def read_places_from_cloud(path: str | Path, bbox: BBox | None = None) -> pd.DataFrame:
    import fsspec

    LOGGER.info("reading_overture_geo", path=str(path))
    with fsspec.open(path, mode="rb") as handle:
        frame = pd.read_parquet(handle)
    if bbox:
        frame = apply_bbox_filter(frame, bbox=bbox)
    return frame


def apply_bbox_filter(frame: pd.DataFrame, bbox: BBox) -> pd.DataFrame:
    min_lon, min_lat, max_lon, max_lat = bbox
    mask = (frame["lon"] >= min_lon) & (frame["lon"] <= max_lon) & (frame["lat"] >= min_lat) & (frame["lat"] <= max_lat)
    return frame[mask]


def filter_operating(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[frame.get("operating_status", "open") == "open"].copy()


def extract_fields(frame: pd.DataFrame) -> pd.DataFrame:
    columns = {
        "id": "poi_id",
        "name": "name",
        "categories": "categories",
        "primary_category": "primary_category",
        "alternate_categories": "alternate_categories",
        "brand": "brand",
        "confidence": "confidence",
        "lat": "lat",
        "lon": "lon",
        "opening_hours": "opening_hours",
    }
    extracted = frame[[col for col in columns if col in frame.columns]].rename(columns=columns)
    if "categories" not in extracted.columns and "primary_category" in extracted.columns:
        extracted["categories"] = extracted["primary_category"].apply(lambda value: [value] if isinstance(value, str) else [])
    return extracted


@dataclass
class PlacesPipeline:
    matcher: CategoryMatcher
    dedupe_config: DedupeConfig = field(default_factory=DedupeConfig)

    def run(
        self,
        frame: pd.DataFrame,
        output_path: Optional[Path] = None,
        hex_resolution: int = 9,
    ) -> gpd.GeoDataFrame:
        working = filter_operating(frame)
        working = extract_fields(working)
        working = self.matcher.assign(working, primary_column="primary_category", alternate_column="alternate_categories")
        deduped = deduplicate_pois(working, config=self.dedupe_config)
        hexed = points_to_hex(deduped, lat_column="lat", lon_column="lon", hex_column="hex_id", resolution=hex_resolution)
        geo = gpd.GeoDataFrame(hexed, geometry=[Point(lon, lat) for lat, lon in zip(hexed["lat"], hexed["lon"])], crs="EPSG:4326")
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            geo.to_parquet(output_path)
        return geo


def load_default_pipeline(crosswalk_path: Path | str = Path("docs/AUCS place category crosswalk")) -> PlacesPipeline:
    matcher = load_crosswalk(crosswalk_path)
    return PlacesPipeline(matcher=matcher)


def ingest_places(
    source: pd.DataFrame | str | Path,
    crosswalk_path: Path | str = Path("docs/AUCS place category crosswalk"),
    bbox: BBox | None = None,
    output_path: Optional[Path] = Path("data/processed/pois.parquet"),
) -> gpd.GeoDataFrame:
    if isinstance(source, (str, Path)):
        frame = read_places_from_cloud(source, bbox=bbox)
    else:
        frame = source
        if bbox:
            frame = apply_bbox_filter(frame, bbox=bbox)
    pipeline = load_default_pipeline(crosswalk_path)
    return pipeline.run(frame, output_path=output_path)


def _bbox_to_wkt(bbox: BBox) -> str:
    min_lon, min_lat, max_lon, max_lat = bbox
    return f"POLYGON(({min_lon} {min_lat}, {max_lon} {min_lat}, {max_lon} {max_lat}, {min_lon} {max_lat}, {min_lon} {min_lat}))"


__all__ = [
    "BigQueryConfig",
    "build_bigquery_query",
    "read_places_from_bigquery",
    "read_places_from_cloud",
    "filter_operating",
    "extract_fields",
    "PlacesPipeline",
    "load_default_pipeline",
    "ingest_places",
]
