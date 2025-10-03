# Implementation Tasks: Add UI Module Test Coverage

## 1. Test Infrastructure Setup

- [ ] 1.1 Install Dash testing dependencies (if not present): `micromamba install -p ./.venv -c conda-forge dash-testing-stub selenium`
- [ ] 1.2 Create `tests/ui/` directory structure
- [ ] 1.3 Create `tests/fixtures/ui_samples.py` for mock datasets
- [ ] 1.4 Define shared UI fixtures in `tests/ui/conftest.py`

## 2. Hex Selection Testing (High Priority - Currently 0%)

- [ ] 2.1 Create `tests/ui/test_hex_selection.py`
  - [ ] Test single hex selection by hex_id
  - [ ] Test multi-hex selection (list of hex_ids)
  - [ ] Test hex deselection (removing from selection)
  - [ ] Test clearing all selections
  - [ ] Test selection limit enforcement (max 100 hexes)
  - [ ] Test selection state serialization to JSON
  - [ ] Test selection state deserialization from JSON
  - [ ] Test invalid hex_id handling
  - [ ] Test selection with duplicate hex_ids (deduplication)
  - [ ] Test selection persistence across page navigation (if applicable)

## 3. Hex Geometry Cache Testing (High Priority)

- [ ] 3.1 Create `tests/ui/test_hexes_extended.py`
  - [ ] Test H3 boundary generation for resolution 9
  - [ ] Test centroid calculation from boundary
  - [ ] Test WKT serialization of hex boundaries
  - [ ] Test geometry cache hit/miss behavior
  - [ ] Test batch geometry generation (1000 hexes at once)
  - [ ] Test handling of invalid H3 IDs (malformed strings)
  - [ ] Test cross-resolution lookups (parent/child hex relationships)
  - [ ] Test cache invalidation when resolution changes
  - [ ] Test memory usage with 10K+ cached geometries
  - [ ] Test thread-safety of cache access (concurrent reads)

## 4. Data Loader Extended Testing (High Priority)

- [ ] 4.1 Extend `tests/test_ui_data_loader.py`
  - [ ] Test dataset version switching:
    - [ ] Load version A, verify data
    - [ ] Switch to version B, verify data changed
    - [ ] Switch back to version A, verify cached or reloaded
  - [ ] Test concurrent version loads (simulate race condition)
  - [ ] Test large dataset loading (1M rows):
    - [ ] Verify memory efficiency (< 500MB for 1M rows)
    - [ ] Verify load time (< 10s)
  - [ ] Test corrupted Parquet file handling:
    - [ ] File with invalid schema → graceful error
    - [ ] Truncated file → clear error message
  - [ ] Test metadata merging:
    - [ ] Scores with 1000 hexes, metadata with 800 → 800 merged rows
    - [ ] Handle missing metadata gracefully
  - [ ] Test bounds calculation:
    - [ ] With all valid geometries → correct bounds
    - [ ] With null geometries → skip nulls, compute bounds from valid
    - [ ] With empty dataset → bounds = None
  - [ ] Test overlay rebuilding:
    - [ ] With shapely installed → overlays built
    - [ ] Without shapely (ImportError) → overlays empty, warning logged
  - [ ] Test cache invalidation:
    - [ ] After data refresh, aggregation cache cleared
    - [ ] After resolution change, viewport cache cleared
  - [ ] Test export:
    - [ ] CSV export with 100K rows completes
    - [ ] GeoJSON export with geometries < 10MB

## 5. Map Layers Testing (Medium Priority)

- [ ] 5.1 Create `tests/ui/test_layers_extended.py`
  - [ ] Test choropleth layer generation:
    - [ ] Default color scale (viridis)
    - [ ] Custom color scale (reds, blues, etc.)
    - [ ] Null/NaN value handling (gray or excluded)
  - [ ] Test hex grid layer:
    - [ ] Resolution 9 grid rendering
    - [ ] Resolution 7 grid (coarser)
    - [ ] Grid updates when resolution changes
  - [ ] Test overlay layer rendering:
    - [ ] Parks overlay with GeoJSON features
    - [ ] Transit overlay with route lines
    - [ ] Overlay toggle on/off
  - [ ] Test viewport-based layer culling:
    - [ ] 100K hexes, viewport shows 1K → layer contains ~1K features
    - [ ] Verify culling performance (< 50ms)
  - [ ] Test layer update performance:
    - [ ] 10K hexes, score update → layer regenerated in < 100ms
  - [ ] Test color scale interpolation:
    - [ ] Score range [0, 100] → colors map linearly
    - [ ] Edge case: all scores equal → single color
    - [ ] Edge case: scores = [0, 0, 100] → two colors used

## 6. Callbacks Testing (High Priority)

- [ ] 6.1 Create `tests/ui/test_callbacks_extended.py`
  - [ ] Test filter updates:
    - [ ] Change state filter → data reloads
    - [ ] Change metro filter → data reloads
    - [ ] Change score range → data reloads
  - [ ] Test viewport change:
    - [ ] Pan map → visible hexes update
    - [ ] Zoom in → more hexes load
    - [ ] Zoom out → fewer hexes shown
  - [ ] Test resolution slider:
    - [ ] Move slider → map detail updates
    - [ ] Resolution 7 → 9 → hexes change
  - [ ] Test overlay toggle:
    - [ ] Enable parks overlay → layer appears
    - [ ] Disable parks overlay → layer hidden
  - [ ] Test selection updates:
    - [ ] Click hex → detail panel updates
    - [ ] Multi-select → panel shows aggregate stats
  - [ ] Test concurrent callbacks:
    - [ ] Simulate rapid filter changes → no race conditions
    - [ ] Verify last change wins
  - [ ] Test callback error handling:
    - [ ] Invalid filter value → error message shown
    - [ ] Data load failure → graceful fallback

## 7. App Initialization Testing (Medium Priority)

- [ ] 7.1 Create `tests/ui/test_app_init.py`
  - [ ] Test Dash app creation with default settings
  - [ ] Test custom UISettings:
    - [ ] Custom data_path → app loads from custom location
    - [ ] Custom port → server binds to custom port
  - [ ] Test layout registration:
    - [ ] All layouts registered (home, map_view, data_management, settings)
    - [ ] Layout IDs unique
  - [ ] Test callback registration:
    - [ ] All callbacks registered without errors
    - [ ] No duplicate callback IDs
  - [ ] Test error handling:
    - [ ] Missing data directory → error message displayed
    - [ ] Invalid configuration → clear error with fix suggestion
  - [ ] Test health check endpoint:
    - [ ] GET /health → 200 OK
    - [ ] Response includes version, data status

## 8. Server Startup Testing (Low Priority)

- [ ] 8.1 Create `tests/ui/test_run.py` (integration test, may be optional)
  - [ ] Test development server startup:
    - [ ] Server starts on default port 8050
    - [ ] Server responds to HTTP requests
  - [ ] Test production server configuration:
    - [ ] Gunicorn/uWSGI config applied (if applicable)
  - [ ] Test port binding:
    - [ ] Port 8050 in use → try 8051, 8052, etc.
    - [ ] Port binding failure → clear error message
  - [ ] Test graceful shutdown:
    - [ ] SIGTERM received → server shuts down cleanly
    - [ ] Active requests complete before shutdown

## 9. Export Testing (Medium Priority)

- [ ] 9.1 Extend `tests/test_ui_export.py`
  - [ ] Test CSV export with all columns
  - [ ] Test GeoJSON export with coordinate precision:
    - [ ] 6 decimal places for lat/lon (default)
    - [ ] Custom precision (e.g., 4 decimal places)
  - [ ] Test large dataset export:
    - [ ] 100K rows to CSV → completes in < 30s
    - [ ] Streaming export for 1M+ rows (chunked writes)
  - [ ] Test export filename generation:
    - [ ] Default: `aucs_export_YYYYMMDD_HHMMSS.csv`
    - [ ] Custom prefix: `my_export_YYYYMMDD.geojson`

## 10. Parameters Testing (Low Priority)

- [ ] 10.1 Extend tests for `ui/parameters.py`
  - [ ] Test parameter validation with invalid types
  - [ ] Test default value fallbacks when user input missing
  - [ ] Test parameter serialization for UI state persistence

## 11. Performance Benchmarking

- [ ] 11.1 Create `tests/ui/test_performance.py` (optional, for CI monitoring)
  - [ ] Benchmark data loading for 1M rows: `assert load_time < 5.0`
  - [ ] Benchmark viewport filtering for 100K hexes: `assert filter_time < 0.1`
  - [ ] Benchmark layer rendering for 10K hexes: `assert render_time < 0.1`
  - [ ] Benchmark overlay generation for state boundaries: `assert overlay_time < 0.5`
  - [ ] Track performance over time (store results in CI artifacts)

## 12. Mock Strategy Implementation

- [ ] 12.1 Create mock fixtures in `tests/ui/conftest.py`:

  ```python
  import pytest
  import pandas as pd
  from Urban_Amenities2.ui.data_loader import DataContext
  from Urban_Amenities2.ui.config import UISettings

  @pytest.fixture
  def mock_data_context(tmp_path):
      # Create mock dataset with 100 rows
      scores = pd.DataFrame({
          "hex_id": [f"8928308280{i:05x}" for i in range(100)],
          "aucs": np.random.uniform(50, 100, 100),
          "EA": np.random.uniform(50, 100, 100),
          # ... other columns
      })
      settings = UISettings(data_path=tmp_path)
      context = DataContext(settings=settings, scores=scores)
      return context

  @pytest.fixture
  def mock_h3_client(monkeypatch):
      # Mock H3 operations for deterministic tests
      def mock_h3_to_geo_boundary(hex_id, geo_json=False):
          # Return fixed boundary for testing
          return [[39.0, -104.0], [39.01, -104.0], [39.01, -104.01], [39.0, -104.01]]
      monkeypatch.setattr("h3.h3_to_geo_boundary", mock_h3_to_geo_boundary)
  ```

## 13. Verification & Coverage Check

- [ ] 13.1 Run UI module tests: `pytest tests/ui/ -v --cov=src/Urban_Amenities2/ui --cov-report=term-missing`
- [ ] 13.2 Verify each submodule meets target:
  - [ ] `ui/hex_selection.py`: ≥90%
  - [ ] `ui/hexes.py`: ≥85%
  - [ ] `ui/data_loader.py`: ≥90%
  - [ ] `ui/layers.py`: ≥85%
  - [ ] `ui/callbacks.py`: ≥85%
  - [ ] `ui/__init__.py`: ≥80%
  - [ ] `ui/run.py`: ≥70%
- [ ] 13.3 Verify overall `ui` module coverage ≥90%
- [ ] 13.4 Run full test suite to ensure no regressions
