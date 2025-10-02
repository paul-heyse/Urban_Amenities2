# Data Ingestion Pipeline for AUCS 2.0

## Why

The AUCS 2.0 model requires diverse geospatial data sources to populate the spatial grid with places, networks, transit, climate, parks, jobs, and education facilities. This change implements robust ETL pipelines for all data sources specified in the data-to-parameter mapping, ensuring data quality, version tracking, and hex-indexed storage.

Without this ingestion layer, we cannot populate the foundational datasets (POIs, network graphs, travel time matrices) required for accessibility scoring.

## What Changes

- Implement Overture Places ingestion with category crosswalk (Overture → AUCS types)
- Implement Overture Transportation ingestion (segments/connectors for routing)
- Implement GTFS static and realtime ingestion for CO/UT/ID transit agencies
- Implement NOAA Climate Normals ingestion for seasonal comfort scoring
- Implement PAD-US and USFS/NPS trails ingestion for parks/outdoors
- Implement LODES jobs data and NCES/IPEDS education data ingestion
- Implement FAA airports and Wikidata/Wikipedia enrichment
- Create deduplic ation, geocoding, and hex-indexing utilities
- Build incremental update mechanisms with change detection
- **BREAKING**: Establishes data contracts and storage formats (Parquet) for all downstream components

## Impact

- Affected specs: `overture-places`, `overture-transportation`, `gtfs-integration`, `climate-data`, `parks-recreation`, `jobs-education-data` (all new)
- Affected code: Creates `src/Urban_Amenities2/` modules:
  - `io/overture/` - Overture Places & Transportation readers
  - `io/gtfs/` - GTFS static/RT parsers (using partridge, gtfs-kit)
  - `io/climate/` - NOAA normals downloader
  - `io/parks/` - PAD-US, USFS, RIDB parsers
  - `io/jobs/` - LODES downloader
  - `io/education/` - NCES, IPEDS, state childcare registries
  - `io/enrichment/` - Wikidata/Wikipedia API clients
  - `xwalk/` - Overture category → AUCS category mapper
  - `dedupe/` - POI deduplication kernels
- Dependencies: Adds duckdb, polars, pyarrow, geopandas, requests, httpx, SPARQLWrapper, partridge, gtfs-kit, rasterio, xarray
- Creates `data/` directory structure: `raw/`, `processed/`, `parquet/` partitioned by source and date
