# Change Proposal: Add UI Module Test Coverage

## Why

The `Urban_Amenities2.ui` module currently has 78.17% test coverage, below the 85% target threshold. The UI is the primary interface for exploring AUCS data, and untested code paths can lead to:

- Silent data loading failures in production
- Broken interactive controls (filters, overlays, viewport navigation)
- Performance regressions from inefficient queries
- State management bugs causing stale data displays

The most critical gaps:

- `ui/hex_selection.py`: 0% coverage (entire module untested)
- `ui/hexes.py`: 57.14% coverage (H3 geometry generation)
- `ui/data_loader.py`: 77.52% coverage (core data management)
- `ui/layers.py`: 70.54% coverage (map layer generation)
- `ui/callbacks.py`: 59.04% coverage (interactive behavior)
- `ui/__init__.py`: 22.86% coverage (app initialization)
- `ui/run.py`: 0% coverage (server startup)

Comprehensive UI testing ensures data integrity, interaction correctness, and performance under realistic usage patterns.

## What Changes

### High-Priority Coverage Additions

**Hex Selection (`ui/hex_selection.py` - Currently 0%):**

- Test hex selection by click on map
- Test multi-hex selection with Shift+click
- Test hex deselection
- Test selection state persistence
- Test clearing all selections
- Test selection limit enforcement (max 100 hexes)
- Test selection serialization/deserialization

**Hex Geometry Cache (`ui/hexes.py`):**

- Test H3 boundary generation for resolution 9
- Test centroid calculation
- Test WKT serialization
- Test geometry cache invalidation
- Test batch geometry generation (1000+ hexes)
- Test handling of invalid H3 IDs
- Test cross-resolution geometry lookups

**Data Loader Extended (`ui/data_loader.py`):**

- Test dataset version switching
- Test concurrent version loads (race conditions)
- Test large dataset loading (1M+ rows)
- Test corrupted Parquet file handling
- Test metadata merging with partial matches
- Test bounds calculation with null geometries
- Test overlay rebuilding with missing shapely
- Test cache invalidation after data refresh
- Test export to CSV/GeoJSON with large datasets

**Map Layers (`ui/layers.py`):**

- Test choropleth layer generation with custom color scales
- Test hex grid layer with resolution switching
- Test overlay layer rendering (parks, transit)
- Test viewport-based layer culling
- Test layer update performance (< 100ms for 10K hexes)
- Test handling of null/NaN values in score data
- Test color scale interpolation edge cases

**Callbacks (`ui/callbacks.py`):**

- Test filter updates trigger data reload
- Test viewport change updates visible hexes
- Test resolution slider updates map detail
- Test overlay toggle updates layer visibility
- Test selection updates hex detail panel
- Test concurrent callback execution (no race conditions)
- Test callback error handling (graceful degradation)

**App Initialization (`ui/__init__.py`):**

- Test Dash app creation with default settings
- Test custom UISettings propagation
- Test layout registration
- Test callback registration
- Test error handling for missing data directory
- Test health check endpoint setup

**Server Startup (`ui/run.py`):**

- Test development server startup
- Test production server configuration
- Test port binding and conflict handling
- Test graceful shutdown
- Test hot reload configuration

### Medium-Priority Coverage Additions

**Export (`ui/export.py`):**

- Test CSV export with all columns (77.78% → 90%)
- Test GeoJSON export with coordinate precision
- Test large dataset export (streaming, chunking)
- Test export filename generation

**Parameters (`ui/parameters.py`):**

- Test parameter validation (90.41% → 95%)
- Test default value fallbacks

**Data Context Extended:**

- Test `apply_viewport` with null bounds
- Test `frame_for_resolution` with invalid resolution
- Test aggregation cache hit rate

### Testing Strategy

**Component Testing with Dash Testing:**

- Use `dash.testing.application_runners.import_app` to test Dash components
- Use `dash.testing.browser.Browser` for integration tests (optional, heavy)
- Mock `DataContext` for isolated component tests

**Mock Strategy:**

- Mock file I/O for Parquet loading (use in-memory DataFrames)
- Mock H3 operations with deterministic hex IDs
- Mock Shapely/GeoPandas for geometry tests
- Use fixtures for sample datasets (100 rows, 1K rows, 100K rows)

**Performance Testing:**

- Benchmark data loading for 1M row dataset (target: < 5s)
- Benchmark viewport filtering for 100K hexes (target: < 100ms)
- Benchmark layer rendering for 10K hexes (target: < 100ms)
- Benchmark overlay generation for state boundaries (target: < 500ms)

**State Management Testing:**

- Test data version switching doesn't corrupt state
- Test filter application order independence
- Test concurrent user interactions (simulated with threads)

### Coverage Targets

- `ui/hex_selection.py`: 0% → 90%
- `ui/hexes.py`: 57.14% → 85%
- `ui/data_loader.py`: 77.52% → 90%
- `ui/layers.py`: 70.54% → 85%
- `ui/callbacks.py`: 59.04% → 85%
- `ui/__init__.py`: 22.86% → 80%
- `ui/run.py`: 0% → 70% (server startup is inherently hard to test)
- **Overall `ui` module: 78.17% → 90%+**

## Impact

**Affected specs:**

- `specs/testing/spec.md` (add UI testing requirements)
- `specs/ui-framework/spec.md` (clarify component contracts)
- `specs/visualization/spec.md` (document layer rendering expectations)
- `specs/caching/spec.md` (specify cache behavior)

**Affected code:**

- `src/Urban_Amenities2/ui/` (test additions only)
- New test files in `tests/ui/` (expand existing coverage)
- Shared fixtures in `tests/fixtures/ui_samples.py` for mock datasets

**Benefits:**

- Increased confidence in UI correctness under user interactions
- Earlier detection of performance regressions
- Protection against state management bugs
- Documented expected behavior through tests

**Risks:**

- UI tests can be brittle (mitigate with robust selectors and abstractions)
- Dash testing can be slow (use unit tests for components, integration tests sparingly)
- Mock-heavy tests may not reflect real behavior (balance with end-to-end tests)

**Migration:**

- No production code changes
- Existing tests remain unchanged
- New tests added to expand coverage
