## 1. Overture Places Ingestion

- [x] 1.1 Create `src/Urban_Amenities2/io/overture/places.py` with:
  - [x] 1.1.1 BigQuery reader for Overture Places theme (state bbox filtering)
  - [x] 1.1.2 S3/Azure reader for Overture Places GeoParquet
  - [x] 1.1.3 Filter by `operating_status='open'`
  - [x] 1.1.4 Extract fields: id, name, categories, brand, confidence, lat/lon, opening_hours
- [x] 1.2 Create `src/Urban_Amenities2/xwalk/overture_aucs.py` with:
  - [x] 1.2.1 Load category crosswalk YAML (from docs/AUCS place category crosswalk)
  - [x] 1.2.2 Implement prefix-based category matcher
  - [x] 1.2.3 Apply inclusion/exclusion rules
  - [x] 1.2.4 Assign aucstype to each POI
- [x] 1.3 Create `src/Urban_Amenities2/dedupe/pois.py` with:
  - [x] 1.3.1 Brand-proximity deduplication (E8 formula)
  - [x] 1.3.2 Name/address fuzzy matching (rapidfuzz)
  - [x] 1.3.3 Distance threshold per category
- [x] 1.4 Index POIs to H3 hexes and write `data/processed/pois.parquet`
- [x] 1.5 Write tests and data quality checks

## 2. Overture Transportation Ingestion

- [x] 2.1 Create `src/Urban_Amenities2/io/overture/transportation.py` with:
  - [x] 2.1.1 BigQuery/S3 reader for Transportation segments
  - [x] 2.1.2 Filter by class, subtype (road, footway, cycleway)
  - [x] 2.1.3 Extract speed_limits, access_restrictions, connectors
  - [x] 2.1.4 Parse geometry (LineString)
- [x] 2.2 Index segments to H3 hexes (midpoint method)
- [x] 2.3 Export for OSRM preprocessing: `data/processed/network_{car,foot,bike}.geojson`
- [x] 2.4 Write tests

## 3. GTFS Integration

- [x] 3.1 Create `src/Urban_Amenities2/io/gtfs/registry.py` with:
  - [x] 3.1.1 Load CO/UT/ID agency registry (from docs or Transitland query)
  - [x] 3.1.2 Store agency metadata: name, state, modes, static_url, rt_urls, license
- [x] 3.2 Create `src/Urban_Amenities2/io/gtfs/static.py` with:
  - [x] 3.2.1 Download GTFS zip for each agency (with caching)
  - [x] 3.2.2 Parse using partridge: stops, routes, trips, stop_times, calendar
  - [x] 3.2.3 Compute headways and service span using gtfs-kit
  - [x] 3.2.4 Index stops to H3 hexes
  - [x] 3.2.5 Write `data/processed/gtfs_stops.parquet`, `gtfs_routes.parquet`, `gtfs_headways.parquet`
- [x] 3.3 Create `src/Urban_Amenities2/io/gtfs/realtime.py` with:
  - [x] 3.3.1 Fetch GTFS-RT feeds (TripUpdates, VehiclePositions, Alerts)
  - [x] 3.3.2 Parse protobuf using gtfs-realtime-bindings
  - [x] 3.3.3 Compute on-time metrics and headway adherence
  - [x] 3.3.4 Write `data/processed/gtfs_reliability.parquet`
- [x] 3.4 Write tests

## 4. Climate Data (NOAA Normals)

- [x] 4.1 Create `src/Urban_Amenities2/io/climate/noaa.py` with:
  - [x] 4.1.1 Query NOAA NCEI API for 1991-2020 normals by station
  - [x] 4.1.2 Download monthly temperature, precipitation, wind
  - [x] 4.1.3 Interpolate to H3 grid (nearest station or spatial interpolation)
  - [x] 4.1.4 Compute "comfortable outdoor days" index per month
  - [x] 4.1.5 Write `data/processed/climate_comfort.parquet`
- [x] 4.2 Write tests

## 5. Parks and Recreation

- [x] 5.1 Create `src/Urban_Amenities2/io/parks/padus.py` with:
  - [x] 5.1.1 Download PAD-US 4.x geodatabase or query ArcGIS FeatureServer
  - [x] 5.1.2 Filter by Access='Open' and state
  - [x] 5.1.3 Compute access points (polygon centroids or entrances)
  - [x] 5.1.4 Index to H3 hexes (area-weighted for large parks)
  - [x] 5.1.5 Write `data/processed/parks.parquet`
- [x] 5.2 Create `src/Urban_Amenities2/io/parks/trails.py` with:
  - [x] 5.2.1 Query USFS EDW for trails (feature service)
  - [x] 5.2.2 Index trail lines to H3 hexes (sample points method)
  - [x] 5.2.3 Write `data/processed/trails.parquet`
- [x] 5.3 Create `src/Urban_Amenities2/io/parks/ridb.py` for recreation areas
- [x] 5.4 Write tests

## 6. Jobs Data (LODES)

- [x] 6.1 Create `src/Urban_Amenities2/io/jobs/lodes.py` with:
  - [x] 6.1.1 Download LODES v8 WAC files for CO, UT, ID from LEHD
  - [x] 6.1.2 Load block-level job counts by NAICS sector
  - [x] 6.1.3 Geocode Census blocks (TIGER/Line centroids)
  - [x] 6.1.4 Allocate jobs to H3 hexes (area-weighted or centroid method)
  - [x] 6.1.5 Write `data/processed/jobs_by_hex.parquet`
- [x] 6.2 Write tests

## 7. Education Data

- [x] 7.1 Create `src/Urban_Amenities2/io/education/nces.py` with:
  - [x] 7.1.1 Download NCES CCD (public schools) and PSS (private schools)
  - [x] 7.1.2 Use NCES EDGE geocodes for lat/lon
  - [x] 7.1.3 Extract: school_id, name, level, enrollment, student_teacher_ratio
  - [x] 7.1.4 Index to H3 hexes
  - [x] 7.1.5 Write `data/processed/schools.parquet`
- [x] 7.2 Create `src/Urban_Amenities2/io/education/ipeds.py` with:
  - [x] 7.2.1 Download IPEDS institutional directory
  - [x] 7.2.2 Load Carnegie 2021 classifications (R1/R2/Doctoral)
  - [x] 7.2.3 Geocode campuses
  - [x] 7.2.4 Compute q_u weights by Carnegie tier
  - [x] 7.2.5 Index to H3 and write `data/processed/universities.parquet`
- [x] 7.3 Create `src/Urban_Amenities2/io/education/childcare.py` for state registries (CO/UT/ID)
- [x] 7.4 Write tests

## 8. Airports (FAA)

- [x] 8.1 Create `src/Urban_Amenities2/io/airports/faa.py` with:
  - [x] 8.1.1 Parse FAA CY2023 Enplanements PDF/Excel
  - [x] 8.1.2 Filter to CO/UT/ID airports (DEN, SLC, BOI, etc.)
  - [x] 8.1.3 Geocode airports (known coordinates)
  - [x] 8.1.4 Compute airport weights from enplanements
  - [x] 8.1.5 Index to H3 and write `data/processed/airports.parquet`
- [x] 8.2 Write tests

## 9. Wikidata/Wikipedia Enrichment

- [x] 9.1 Create `src/Urban_Amenities2/io/enrichment/wikidata.py` with:
  - [x] 9.1.1 SPARQL query builder for entity reconciliation
  - [x] 9.1.2 Match POIs to Wikidata QIDs (via brand or coordinates)
  - [x] 9.1.3 Extract properties: P1083 (capacity), heritage status
- [x] 9.2 Create `src/Urban_Amenities2/io/enrichment/wikipedia.py` with:
  - [x] 9.2.1 Wikimedia Pageviews API client
  - [x] 9.2.2 Fetch 12-month rolling pageview medians for matched attractions
  - [x] 9.2.3 Compute popularity z-scores by category
  - [x] 9.2.4 Compute IQR for novelty scoring
- [x] 9.3 Join enrichment data to POIs and update `pois.parquet`
- [x] 9.4 Write tests

## 10. Incremental Updates & Versioning

- [x] 10.1 Create `src/Urban_Amenities2/io/versioning/snapshots.py` with:
  - [x] 10.1.1 Compute file hashes (SHA256) for all downloaded data
  - [x] 10.1.2 Record download timestamps and source versions
  - [x] 10.1.3 Detect changes (diff against previous snapshots)
  - [x] 10.1.4 Store snapshot registry in `data/snapshots.jsonl`
- [x] 10.2 Implement incremental update logic (download only if changed)
- [x] 10.3 Write tests

## 11. Data Quality Checks

- [x] 11.1 Create `src/Urban_Amenities2/io/quality/checks.py` with:
  - [x] 11.1.1 Coverage checks (POIs per hex, transit stops per metro)
  - [x] 11.1.2 Completeness checks (required fields, category distribution)
  - [x] 11.1.3 Validity checks (coordinate bounds, hex resolution, date ranges)
  - [x] 11.1.4 Consistency checks (cross-dataset joins, deduplication rates)
- [x] 11.2 Generate data quality reports in `data/quality_reports/`
- [x] 11.3 Write tests

## 12. CLI Integration

- [x] 12.1 Add `aucs ingest overture-places --state CO --bbox ...` command
- [x] 12.2 Add `aucs ingest gtfs --agency RTD` command
- [x] 12.3 Add `aucs ingest all --states CO,UT,ID` command for full pipeline
- [x] 12.4 Add `aucs data quality-report` command
- [x] 12.5 Add `aucs data list-snapshots` command
- [x] 12.6 Write tests for CLI commands

## 13. Documentation

- [x] 13.1 Write `docs/data_sources.md` listing all sources, endpoints, licenses
- [x] 13.2 Write `docs/data_pipeline.md` explaining ETL flow and data quality
- [x] 13.3 Document category crosswalk usage in `docs/categories.md`
- [x] 13.4 Create example scripts in `examples/ingest_co_data.py`
- [x] 13.5 Update main README with data ingestion instructions
