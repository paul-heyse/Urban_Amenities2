# Data Sources

This document summarises the data feeds consumed by the Urban Amenities model and
how they map to the ingestion modules implemented in `src/Urban_Amenities2/io`.
It complements the in-code docstrings and the crosswalk stored in
`docs/AUCS place category crosswalk`.

## Overture

| Dataset | Module | Notes |
|---------|--------|-------|
| Places (BigQuery/GeoParquet) | `io.overture.places` | Filters to `operating_status='open'`, extracts name/brand/category, applies AUCS crosswalk, deduplicates POIs, indexes to H3, writes `data/processed/pois.parquet`. |
| Transportation segments | `io.overture.transportation` | Supports BigQuery or object storage parquet. Filters to `{road, footway, cycleway}`, parses `LineString` geometry, assigns mode flags, exports GeoJSON for OSRM preprocessing. |

## Transit (GTFS)

| Dataset | Module | Outputs |
|---------|--------|---------|
| Agency registry (static + realtime endpoints) | `io.gtfs.registry` | Loads Colorado/Utah/Idaho agencies and metadata used by other modules. |
| GTFS Static feeds | `io.gtfs.static` | Downloads feeds with caching + snapshotting, parses stops/routes/trips/calendar, computes headways and service spans, indexes stops to H3, writes `gtfs_stops.parquet`, `gtfs_routes.parquet`, `gtfs_headways.parquet`. |
| GTFS Realtime feeds | `io.gtfs.realtime` | Fetches TripUpdates/VehiclePositions/Alerts, records snapshots, computes delay and on-time metrics, writes `gtfs_reliability.parquet`. |

## Climate

| Dataset | Module | Outputs |
|---------|--------|---------|
| NOAA NCEI 1991–2020 Normals API | `io.climate.noaa` | Queries monthly temperature, precipitation, and wind normals per station, interpolates to H3, computes "comfortable outdoor days" index, writes `climate_comfort.parquet`. |

## Parks & Recreation

| Dataset | Module | Notes |
|---------|--------|-------|
| PAD-US 4.x | `io.parks.padus` | Reads geodatabase/FeatureServer, filters `Access='Open'`, calculates centroids/access points, indexes polygons to H3 with area-weight handling. |
| USFS Trails (EDW) | `io.parks.trails` | Queries line features, samples points along trail geometry, indexes to H3. |
| Recreation.gov RIDB | `io.parks.ridb` | Paginates API per state, records snapshots, indexes recreation areas to H3. |

## Jobs & Education

| Dataset | Module | Outputs |
|---------|--------|---------|
| LODES v8 (WAC) | `io.jobs.lodes` | Downloads compressed CSV, joins block centroids, allocates jobs to H3, writes `jobs_by_hex.parquet`. |
| NCES CCD/PSS + EDGE geocodes | `io.education.nces` | Harmonises public/private school registries, assigns levels, computes ratios, indexes to H3, writes `schools.parquet`. |
| IPEDS directory + Carnegie 2021 | `io.education.ipeds` | Merges campus coordinates with Carnegie tiers, computes quality weights, writes `universities.parquet`. |
| State childcare registries | `io.education.childcare` | Normalises state-level provider extracts, unifies schema, indexes to H3, writes `childcare.parquet`. |

## Airports

| Dataset | Module | Outputs |
|---------|--------|---------|
| FAA CY2023 Enplanements | `io.airports.faa` | Parses Excel/PDF extracts, filters to CO/UT/ID airports, geocodes, computes passenger weights, writes `airports.parquet`. |

## Enrichment & Quality

| Dataset | Module | Notes |
|---------|--------|-------|
| Wikidata SPARQL | `io.enrichment.wikidata` | Matches POIs via brand/coordinates, extracts capacity and heritage attributes. |
| Wikimedia Pageviews | `io.enrichment.wikipedia` | Fetches per-article pageviews, computes medians/IQRs and popularity z-scores. |
| Quality Checks | `io.quality.checks` | Aggregates coverage/completeness/validity metrics, produces `data/quality_reports/` outputs. |
| Snapshot Registry | `io.versioning.snapshots` | Hash-based change tracking for all downloads in `data/snapshots.jsonl`. |

For additional context, see `docs/data_pipeline.md` and `docs/categories.md`.
