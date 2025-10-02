## 1. Overture Places Ingestion

- [ ] 1.1 Create `src/Urban_Amenities2/io/overture/places.py` with:
  - [ ] 1.1.1 BigQuery reader for Overture Places theme (state bbox filtering)
  - [ ] 1.1.2 S3/Azure reader for Overture Places GeoParquet
  - [ ] 1.1.3 Filter by `operating_status='open'`
  - [ ] 1.1.4 Extract fields: id, name, categories, brand, confidence, lat/lon, opening_hours
- [ ] 1.2 Create `src/Urban_Amenities2/xwalk/overture_aucs.py` with:
  - [ ] 1.2.1 Load category crosswalk YAML (from docs/AUCS place category crosswalk)
  - [ ] 1.2.2 Implement prefix-based category matcher
  - [ ] 1.2.3 Apply inclusion/exclusion rules
  - [ ] 1.2.4 Assign aucstype to each POI
- [ ] 1.3 Create `src/Urban_Amenities2/dedupe/pois.py` with:
  - [ ] 1.3.1 Brand-proximity deduplication (E8 formula)
  - [ ] 1.3.2 Name/address fuzzy matching (rapidfuzz)
  - [ ] 1.3.3 Distance threshold per category
- [ ] 1.4 Index POIs to H3 hexes and write `data/processed/pois.parquet`
- [ ] 1.5 Write tests and data quality checks

## 2. Overture Transportation Ingestion

- [ ] 2.1 Create `src/Urban_Amenities2/io/overture/transportation.py` with:
  - [ ] 2.1.1 BigQuery/S3 reader for Transportation segments
  - [ ] 2.1.2 Filter by class, subtype (road, footway, cycleway)
  - [ ] 2.1.3 Extract speed_limits, access_restrictions, connectors
  - [ ] 2.1.4 Parse geometry (LineString)
- [ ] 2.2 Index segments to H3 hexes (midpoint method)
- [ ] 2.3 Export for OSRM preprocessing: `data/processed/network_{car,foot,bike}.geojson`
- [ ] 2.4 Write tests

## 3. GTFS Integration

- [ ] 3.1 Create `src/Urban_Amenities2/io/gtfs/registry.py` with:
  - [ ] 3.1.1 Load CO/UT/ID agency registry (from docs or Transitland query)
  - [ ] 3.1.2 Store agency metadata: name, state, modes, static_url, rt_urls, license
- [ ] 3.2 Create `src/Urban_Amenities2/io/gtfs/static.py` with:
  - [ ] 3.2.1 Download GTFS zip for each agency (with caching)
  - [ ] 3.2.2 Parse using partridge: stops, routes, trips, stop_times, calendar
  - [ ] 3.2.3 Compute headways and service span using gtfs-kit
  - [ ] 3.2.4 Index stops to H3 hexes
  - [ ] 3.2.5 Write `data/processed/gtfs_stops.parquet`, `gtfs_routes.parquet`, `gtfs_headways.parquet`
- [ ] 3.3 Create `src/Urban_Amenities2/io/gtfs/realtime.py` with:
  - [ ] 3.3.1 Fetch GTFS-RT feeds (TripUpdates, VehiclePositions, Alerts)
  - [ ] 3.3.2 Parse protobuf using gtfs-realtime-bindings
  - [ ] 3.3.3 Compute on-time metrics and headway adherence
  - [ ] 3.3.4 Write `data/processed/gtfs_reliability.parquet`
- [ ] 3.4 Write tests

## 4. Climate Data (NOAA Normals)

- [ ] 4.1 Create `src/Urban_Amenities2/io/climate/noaa.py` with:
  - [ ] 4.1.1 Query NOAA NCEI API for 1991-2020 normals by station
  - [ ] 4.1.2 Download monthly temperature, precipitation, wind
  - [ ] 4.1.3 Interpolate to H3 grid (nearest station or spatial interpolation)
  - [ ] 4.1.4 Compute "comfortable outdoor days" index per month
  - [ ] 4.1.5 Write `data/processed/climate_comfort.parquet`
- [ ] 4.2 Write tests

## 5. Parks and Recreation

- [ ] 5.1 Create `src/Urban_Amenities2/io/parks/padus.py` with:
  - [ ] 5.1.1 Download PAD-US 4.x geodatabase or query ArcGIS FeatureServer
  - [ ] 5.1.2 Filter by Access='Open' and state
  - [ ] 5.1.3 Compute access points (polygon centroids or entrances)
  - [ ] 5.1.4 Index to H3 hexes (area-weighted for large parks)
  - [ ] 5.1.5 Write `data/processed/parks.parquet`
- [ ] 5.2 Create `src/Urban_Amenities2/io/parks/trails.py` with:
  - [ ] 5.2.1 Query USFS EDW for trails (feature service)
  - [ ] 5.2.2 Index trail lines to H3 hexes (sample points method)
  - [ ] 5.2.3 Write `data/processed/trails.parquet`
- [ ] 5.3 Create `src/Urban_Amenities2/io/parks/ridb.py` for recreation areas
- [ ] 5.4 Write tests

## 6. Jobs Data (LODES)

- [ ] 6.1 Create `src/Urban_Amenities2/io/jobs/lodes.py` with:
  - [ ] 6.1.1 Download LODES v8 WAC files for CO, UT, ID from LEHD
  - [ ] 6.1.2 Load block-level job counts by NAICS sector
  - [ ] 6.1.3 Geocode Census blocks (TIGER/Line centroids)
  - [ ] 6.1.4 Allocate jobs to H3 hexes (area-weighted or centroid method)
  - [ ] 6.1.5 Write `data/processed/jobs_by_hex.parquet`
- [ ] 6.2 Write tests

## 7. Education Data

- [ ] 7.1 Create `src/Urban_Amenities2/io/education/nces.py` with:
  - [ ] 7.1.1 Download NCES CCD (public schools) and PSS (private schools)
  - [ ] 7.1.2 Use NCES EDGE geocodes for lat/lon
  - [ ] 7.1.3 Extract: school_id, name, level, enrollment, student_teacher_ratio
  - [ ] 7.1.4 Index to H3 hexes
  - [ ] 7.1.5 Write `data/processed/schools.parquet`
- [ ] 7.2 Create `src/Urban_Amenities2/io/education/ipeds.py` with:
  - [ ] 7.2.1 Download IPEDS institutional directory
  - [ ] 7.2.2 Load Carnegie 2021 classifications (R1/R2/Doctoral)
  - [ ] 7.2.3 Geocode campuses
  - [ ] 7.2.4 Compute q_u weights by Carnegie tier
  - [ ] 7.2.5 Index to H3 and write `data/processed/universities.parquet`
- [ ] 7.3 Create `src/Urban_Amenities2/io/education/childcare.py` for state registries (CO/UT/ID)
- [ ] 7.4 Write tests

## 8. Airports (FAA)

- [ ] 8.1 Create `src/Urban_Amenities2/io/airports/faa.py` with:
  - [ ] 8.1.1 Parse FAA CY2023 Enplanements PDF/Excel
  - [ ] 8.1.2 Filter to CO/UT/ID airports (DEN, SLC, BOI, etc.)
  - [ ] 8.1.3 Geocode airports (known coordinates)
  - [ ] 8.1.4 Compute airport weights from enplanements
  - [ ] 8.1.5 Index to H3 and write `data/processed/airports.parquet`
- [ ] 8.2 Write tests

## 9. Wikidata/Wikipedia Enrichment

- [ ] 9.1 Create `src/Urban_Amenities2/io/enrichment/wikidata.py` with:
  - [ ] 9.1.1 SPARQL query builder for entity reconciliation
  - [ ] 9.1.2 Match POIs to Wikidata QIDs (via brand or coordinates)
  - [ ] 9.1.3 Extract properties: P1083 (capacity), heritage status
- [ ] 9.2 Create `src/Urban_Amenities2/io/enrichment/wikipedia.py` with:
  - [ ] 9.2.1 Wikimedia Pageviews API client
  - [ ] 9.2.2 Fetch 12-month rolling pageview medians for matched attractions
  - [ ] 9.2.3 Compute popularity z-scores by category
  - [ ] 9.2.4 Compute IQR for novelty scoring
- [ ] 9.3 Join enrichment data to POIs and update `pois.parquet`
- [ ] 9.4 Write tests

## 10. Incremental Updates & Versioning

- [ ] 10.1 Create `src/Urban_Amenities2/io/versioning/snapshots.py` with:
  - [ ] 10.1.1 Compute file hashes (SHA256) for all downloaded data
  - [ ] 10.1.2 Record download timestamps and source versions
  - [ ] 10.1.3 Detect changes (diff against previous snapshots)
  - [ ] 10.1.4 Store snapshot registry in `data/snapshots.jsonl`
- [ ] 10.2 Implement incremental update logic (download only if changed)
- [ ] 10.3 Write tests

## 11. Data Quality Checks

- [ ] 11.1 Create `src/Urban_Amenities2/io/quality/checks.py` with:
  - [ ] 11.1.1 Coverage checks (POIs per hex, transit stops per metro)
  - [ ] 11.1.2 Completeness checks (required fields, category distribution)
  - [ ] 11.1.3 Validity checks (coordinate bounds, hex resolution, date ranges)
  - [ ] 11.1.4 Consistency checks (cross-dataset joins, deduplication rates)
- [ ] 11.2 Generate data quality reports in `data/quality_reports/`
- [ ] 11.3 Write tests

## 12. CLI Integration

- [ ] 12.1 Add `aucs ingest overture-places --state CO --bbox ...` command
- [ ] 12.2 Add `aucs ingest gtfs --agency RTD` command
- [ ] 12.3 Add `aucs ingest all --states CO,UT,ID` command for full pipeline
- [ ] 12.4 Add `aucs data quality-report` command
- [ ] 12.5 Add `aucs data list-snapshots` command
- [ ] 12.6 Write tests for CLI commands

## 13. Documentation

- [ ] 13.1 Write `docs/data_sources.md` listing all sources, endpoints, licenses
- [ ] 13.2 Write `docs/data_pipeline.md` explaining ETL flow and data quality
- [ ] 13.3 Document category crosswalk usage in `docs/categories.md`
- [ ] 13.4 Create example scripts in `examples/ingest_co_data.py`
- [ ] 13.5 Update main README with data ingestion instructions
