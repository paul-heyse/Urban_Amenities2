# Change Proposal: Add I/O Module Test Coverage

## Why

The `Urban_Amenities2.io` module currently has 72.78% test coverage, below the 75% target threshold. Critical data ingestion paths remain untested, including:

- Overture Places API integration (37.96% coverage)
- Overture Transportation networks (55.08% coverage)
- PAD-US parks data processing (51.28% coverage)
- FAA airport data parsing (50.00% coverage)
- NOAA climate data fetching (63.55% coverage)
- Wikidata enrichment queries (64.94% coverage)

Untested code paths create risk for production data pipelines, where failures can corrupt scoring calculations or cause silent data quality degradation.

## What Changes

### High-Priority Coverage Additions

**Overture Places (`io/overture/places.py`):**

- Test BigQuery result parsing with malformed schemas
- Test category mapping edge cases (unknown categories, null values)
- Test geometry validation failures
- Test pagination and batching logic
- Test deduplication within query results

**Overture Transportation (`io/overture/transportation.py`):**

- Test network segment extraction from nested GeoJSON
- Test road classification mapping
- Test coordinate transformation edge cases
- Test handling of disconnected network components

**Parks Data (`io/parks/`):**

- PAD-US: Test access point derivation from complex polygons
- PAD-US: Test geometry simplification thresholds
- RIDB: Test API pagination and rate limiting
- Trails: Test GPX/KML parsing with invalid coordinates

**Climate Data (`io/climate/noaa.py`):**

- Test station selection by bounding box
- Test handling of incomplete monthly normals
- Test interpolation for missing data points
- Test caching and staleness detection

**Enrichment (`io/enrichment/`):**

- Wikidata: Test SPARQL query construction and error recovery
- Wikipedia: Test pageview API rate limiting
- Test fallback behavior when enrichment sources unavailable

**Education & Jobs (`io/education/`, `io/jobs/`):**

- NCES: Test school data parsing with missing fields
- IPEDS: Test university enrollment data validation
- LODES: Test block-level job counts aggregation
- Childcare: Test state registry format variations

**Quality Checks (`io/quality/checks.py`):**

- Test schema validation failures with detailed error messages
- Test completeness checks for required fields
- Test outlier detection thresholds

### Medium-Priority Coverage Additions

**GTFS Processing:**

- Test realtime feed parsing with protobuf edge cases (85.71% → 95%)
- Test static GTFS validation for malformed agency/routes (85.12% → 95%)

**Airports (`io/airports/faa.py`):**

- Test PDF table extraction robustness
- Test enplanement data year-over-year consistency checks

### Testing Strategy

**Test Organization:**

- Create `tests/io/` subdirectory mirroring `src/Urban_Amenities2/io/` structure
- Use `pytest` fixtures for mock HTTP responses (`responses` library)
- Use property-based testing (`hypothesis`) for geometry/coordinate edge cases

**Mock Strategy:**

- Mock external API calls (BigQuery, NOAA, Wikidata, Wikipedia APIs)
- Use fixture files for sample API responses (JSON, GeoJSON, CSV)
- Create lightweight stubs for `geopandas` and `shapely` operations where performance-critical

**Coverage Targets:**

- `io.overture.places`: 37.96% → 85%
- `io.overture.transportation`: 55.08% → 85%
- `io.parks.padus`: 51.28% → 80%
- `io.airports.faa`: 50.00% → 80%
- `io.climate.noaa`: 63.55% → 85%
- `io.enrichment.wikidata`: 64.94% → 85%
- `io.quality.checks`: 35.14% → 80%
- **Overall `io` module: 72.78% → 85%+**

## Impact

**Affected specs:**

- `specs/testing/spec.md` (add I/O testing requirements)
- `specs/overture-places/spec.md` (clarify error handling contracts)
- `specs/gtfs-integration/spec.md` (document validation expectations)
- `specs/climate-data/spec.md` (specify interpolation behavior)
- `specs/parks-recreation/spec.md` (define geometry processing rules)

**Affected code:**

- All modules under `src/Urban_Amenities2/io/` (test additions only)
- New test files in `tests/io/` (mirror source structure)
- Shared fixtures in `tests/fixtures/io_samples/` for mock API responses

**Benefits:**

- Increased confidence in data pipeline correctness
- Earlier detection of upstream API schema changes
- Reduced production incidents from malformed data
- Improved maintainability with documented expected behavior

**Risks:**

- Test maintenance burden if external APIs change frequently
- Risk of over-mocking leading to tests that don't reflect real API behavior
- Potential slowdown in test suite runtime (mitigated by selective mocking)

**Migration:**

- No code changes to production modules
- Existing tests remain unchanged
- New tests added incrementally per module
