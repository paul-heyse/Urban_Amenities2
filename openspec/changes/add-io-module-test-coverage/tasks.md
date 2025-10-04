# Implementation Tasks: Add I/O Module Test Coverage

## 1. Test Infrastructure Setup

- [x] 1.1 Create `tests/io/` directory structure mirroring `src/Urban_Amenities2/io/`
- [x] 1.2 Install `responses` library for HTTP mocking: `micromamba install -p ./.venv -c conda-forge responses`
- [x] 1.3 Create `tests/fixtures/io_samples/` for sample API responses
- [x] 1.4 Define shared fixtures in `tests/io/conftest.py` (mock sessions, sample geometries, etc.)

## 2. Overture Maps Testing (High Priority)

- [x] 2.1 Create `tests/io/overture/test_places.py`
  - [x] Test BigQuery result parsing with complete and incomplete schemas
  - [x] Test category mapping for all supported Overture categories
  - [x] Test handling of null/missing geometry fields
  - [x] Test deduplication logic when multiple records share coordinates
  - [x] Test pagination with large result sets (>10K POIs)
- [x] 2.2 Create `tests/io/overture/test_transportation.py`
  - [x] Test segment extraction from LineString and MultiLineString geometries
  - [x] Test road classification mapping for all supported types
  - [x] Test coordinate transformation between CRS systems
  - [x] Test handling of disconnected network components
  - [x] Test network simplification for rendering

## 3. Parks & Recreation Testing (High Priority)

- [ ] 3.1 Create `tests/io/parks/test_padus.py`
  - [ ] Test access point derivation from polygon centroids
  - [ ] Test geometry simplification with tolerance thresholds
  - [ ] Test handling of multi-polygon park complexes
  - [ ] Test filtering by park type and access level
- [ ] 3.2 Create `tests/io/parks/test_ridb.py`
  - [x] Test API pagination with cursor-based navigation
  - [ ] Test rate limiting and retry logic
  - [ ] Test facility filtering by activity types
  - [x] Test handling of incomplete facility records
- [ ] 3.3 Create `tests/io/parks/test_trails.py`
  - [ ] Test GPX parsing with valid and malformed tracks
  - [ ] Test KML parsing with nested folder structures
  - [ ] Test trail elevation profile extraction
  - [ ] Test handling of missing or invalid coordinate pairs

## 4. Climate Data Testing (High Priority)

- [x] 4.1 Create `tests/io/climate/test_noaa.py`
  - [ ] Test station selection by geographic bounding box
  - [x] Test monthly normals parsing for all 12 months
  - [x] Test handling of missing data with interpolation fallbacks
  - [x] Test temperature and precipitation unit conversions
  - [ ] Test cache invalidation after staleness threshold
  - [ ] Test parallel station data fetching

## 5. Enrichment Testing (High Priority)

- [x] 5.1 Create `tests/io/enrichment/test_wikidata.py`
  - [x] Test SPARQL query construction for entity resolution
  - [x] Test parsing of Wikidata JSON responses
  - [x] Test handling of entities with no English labels
  - [x] Test timeout and retry logic for slow queries
  - [x] Test batch querying for multiple entities
- [x] 5.2 Create `tests/io/enrichment/test_wikipedia.py`
  - [x] Test pageview API requests with date ranges
  - [x] Test handling of redirects and disambiguation pages
  - [x] Test rate limiting with exponential backoff
  - [x] Test caching of pageview statistics
  - [x] Test fallback to zero pageviews when API unavailable

## 6. Education & Jobs Testing (Medium Priority)

- [ ] 6.1 Create `tests/io/education/test_nces.py`
  - [ ] Test school data CSV parsing with all required columns
  - [ ] Test handling of missing enrollment or rating fields
  - [ ] Test geocoding fallback for schools without coordinates
- [ ] 6.2 Create `tests/io/education/test_ipeds.py`
  - [ ] Test university data extraction from Excel/CSV
  - [ ] Test enrollment aggregation by institution type
  - [ ] Test handling of multi-campus institutions
- [ ] 6.3 Create `tests/io/education/test_childcare.py`
  - [ ] Test state registry format parsing (CO, UT, ID variants)
  - [ ] Test capacity and quality score extraction
- [ ] 6.4 Create `tests/io/jobs/test_lodes.py`
  - [ ] Test LODES WAC/RAC file downloading
  - [ ] Test block-level job count aggregation to hexes
  - [ ] Test industry sector filtering

## 7. Quality Checks Testing (High Priority)

- [x] 7.1 Create `tests/io/quality/test_checks.py`
  - [ ] Test schema validation with Pandera schemas
  - [x] Test completeness checks for required columns
  - [ ] Test outlier detection for numeric fields
  - [x] Test duplicate detection across multiple columns
  - [ ] Test comprehensive error message formatting

## 8. Airports Testing (Medium Priority)

- [ ] 8.1 Create `tests/io/airports/test_faa.py`
  - [ ] Test PDF table extraction from annual reports
  - [ ] Test enplanement data parsing and validation
  - [ ] Test airport code normalization (IATA/ICAO)
  - [ ] Test filtering by minimum enplanement threshold

## 9. GTFS Testing (Low Priority - Already High Coverage)

- [ ] 9.1 Extend `tests/io/gtfs/test_realtime.py`
  - [ ] Add edge case tests for protobuf parsing (85.71% → 95%)
  - [ ] Test handling of malformed or truncated messages
- [ ] 9.2 Extend `tests/io/gtfs/test_static.py`
  - [ ] Add validation tests for malformed agency/routes (85.12% → 95%)
  - [ ] Test handling of GTFS feeds with missing optional files

## 10. Verification & Documentation

- [x] 10.1 Run full test suite: `pytest tests/io/ -v --cov=src/Urban_Amenities2/io --cov-report=term-missing`
- [ ] 10.2 Verify `io` module coverage meets 85% threshold
- [x] 10.3 Update `tests/README.md` with I/O testing patterns and fixtures
- [x] 10.4 Document external API mocking strategy in `AGENTS.md`
