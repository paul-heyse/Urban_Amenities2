# Spec Delta: UI Module Testing Requirements

## ADDED Requirements

### Requirement: Component Isolation Testing

UI components SHALL be tested in isolation using mocked dependencies to ensure deterministic behavior.

#### Scenario: Data loader tested without real Parquet files

- **GIVEN** a test for DataContext data loading
- **WHEN** the test creates a mock DataFrame in memory
- **THEN** the DataContext loads the mock data
- **AND** all filtering and aggregation functions work correctly

#### Scenario: Map layers tested without real H3 library

- **GIVEN** a test for choropleth layer generation
- **WHEN** H3 geometry functions are mocked with fixtures
- **THEN** the layer renders with expected GeoJSON structure
- **AND** the test runs without H3 installation

### Requirement: State Management Testing

UI state changes SHALL be tested to ensure correctness and consistency across component updates.

#### Scenario: Dataset version switch updates all dependent state

- **GIVEN** a DataContext loaded with version "2024-01-01"
- **WHEN** the user switches to version "2024-02-01"
- **THEN** the scores DataFrame is updated
- **AND** the geometries cache is invalidated and rebuilt
- **AND** the aggregation cache is cleared
- **AND** the overlays are regenerated

#### Scenario: Filter changes preserve selection state

- **GIVEN** a user has selected 10 hexes on the map
- **WHEN** the user changes the state filter
- **THEN** the data is filtered
- **AND** the selected hex IDs remain in selection state
- **AND** hexes not matching the filter are visually de-emphasized

### Requirement: Performance Regression Testing

UI operations SHALL be benchmarked to detect performance regressions in data loading, filtering, and rendering.

#### Scenario: Large dataset loads within time budget

- **GIVEN** a Parquet file with 1M rows of score data
- **WHEN** the DataContext loads the file
- **THEN** loading completes in < 10 seconds
- **AND** memory usage remains < 500MB

#### Scenario: Viewport filtering meets responsiveness requirement

- **GIVEN** a dataset with 100K hexes loaded
- **WHEN** the user pans the map viewport
- **THEN** the visible hexes are filtered in < 100ms
- **AND** the map updates without perceptible lag

#### Scenario: Layer rendering scales linearly

- **GIVEN** datasets with 1K, 10K, 100K hexes
- **WHEN** choropleth layers are generated for each
- **THEN** render time scales approximately linearly with hex count
- **AND** 10K hexes render in < 100ms

### Requirement: Concurrent Interaction Testing

UI callbacks SHALL handle concurrent user interactions without race conditions or state corruption.

#### Scenario: Rapid filter changes apply sequentially

- **GIVEN** a user rapidly changes the state filter 5 times
- **WHEN** the callbacks execute
- **THEN** only the final filter value is applied
- **AND** intermediate states do not corrupt the data

#### Scenario: Viewport pan during data load completes cleanly

- **GIVEN** a large dataset is loading (5-second operation)
- **WHEN** the user pans the map viewport during loading
- **THEN** the viewport change queues after data load
- **AND** the final map state reflects both the new data and viewport

### Requirement: Error Handling and Graceful Degradation

UI SHALL handle errors gracefully with user-friendly messages and fallback behavior.

#### Scenario: Missing data directory displays error page

- **GIVEN** the UISettings specify a non-existent data_path
- **WHEN** the app initializes
- **THEN** a user-friendly error message is displayed
- **AND** the message suggests creating the directory or checking the path

#### Scenario: Corrupted Parquet file shows specific error

- **GIVEN** a Parquet file with invalid schema
- **WHEN** the DataContext attempts to load it
- **THEN** a ParquetError is caught
- **AND** the error message identifies the file and issue
- **AND** the app remains functional with no data loaded

#### Scenario: Shapely missing disables overlays gracefully

- **GIVEN** the shapely library is not installed
- **WHEN** the DataContext attempts to build overlays
- **THEN** an ImportError is caught
- **AND** a warning is logged
- **AND** overlays return empty feature collections

### Requirement: Hex Selection Behavior

Hex selection state SHALL support single, multi, and bulk selection with enforcement of selection limits.

#### Scenario: Single hex selection updates state

- **GIVEN** no hexes are currently selected
- **WHEN** the user clicks a hex with ID "8928308280fffff"
- **THEN** the selection state contains ["8928308280fffff"]
- **AND** the hex detail panel displays data for that hex

#### Scenario: Multi-select adds to existing selection

- **GIVEN** hexes ["hex1", "hex2"] are selected
- **WHEN** the user Shift+clicks "hex3"
- **THEN** the selection state becomes ["hex1", "hex2", "hex3"]
- **AND** the detail panel shows aggregate stats for all 3

#### Scenario: Selection limit enforced at 100 hexes

- **GIVEN** 100 hexes are already selected
- **WHEN** the user attempts to select a 101st hex
- **THEN** the selection is rejected
- **AND** a warning message displays: "Maximum 100 hexes can be selected"

#### Scenario: Clear selection empties state

- **GIVEN** hexes ["hex1", "hex2", "hex3"] are selected
- **WHEN** the user clicks "Clear Selection"
- **THEN** the selection state becomes []
- **AND** the hex detail panel displays a "No selection" message

### Requirement: Geometry Cache Efficiency

Hex geometry cache SHALL minimize redundant H3 computations and memory usage.

#### Scenario: Geometry cache hit avoids recomputation

- **GIVEN** hex "8928308280fffff" geometry is cached
- **WHEN** the geometry is requested again
- **THEN** the cached geometry is returned
- **AND** no H3 library call is made

#### Scenario: Batch geometry generation is efficient

- **GIVEN** 1000 hex IDs need geometries
- **WHEN** geometries are requested in batch
- **THEN** all 1000 are computed in a single vectorized call
- **AND** the operation completes in < 500ms

#### Scenario: Cache invalidation clears stale data

- **GIVEN** geometries are cached for resolution 9
- **WHEN** the user switches to resolution 7
- **THEN** the cache is invalidated
- **AND** new geometries are generated for resolution 7

### Requirement: Overlay Generation

Map overlays for state, metro, and county boundaries SHALL be generated from hex data with polygon simplification.

#### Scenario: State overlay generated from hex geometries

- **GIVEN** hexes with state="CO", state="UT"
- **WHEN** the state overlay is built
- **THEN** two features are created (one per state)
- **AND** each feature's geometry is the union of constituent hex polygons
- **AND** polygons are simplified to < 1000 vertices per state

#### Scenario: Missing shapely prevents overlay generation

- **GIVEN** shapely is not installed
- **WHEN** the DataContext attempts to build overlays
- **THEN** no overlays are generated
- **AND** `get_overlay("state")` returns empty feature collection
- **AND** a warning is logged once

#### Scenario: Overlay regeneration triggered by data refresh

- **GIVEN** overlays are built for dataset "2024-01-01"
- **WHEN** the user loads dataset "2024-02-01"
- **THEN** overlays are regenerated with new data
- **AND** the previous overlays are discarded

### Requirement: Export Functionality

Data export to CSV and GeoJSON SHALL handle large datasets with appropriate formatting and filename conventions.

#### Scenario: CSV export includes all score columns

- **GIVEN** a dataset with columns [hex_id, aucs, EA, LCA, ...]
- **WHEN** the user exports to CSV
- **THEN** all columns are included in the output
- **AND** the file is named `aucs_export_{timestamp}.csv`

#### Scenario: GeoJSON export includes geometries

- **GIVEN** a dataset with geometries attached
- **WHEN** the user exports to GeoJSON
- **THEN** each feature has a `geometry` field with coordinates
- **AND** `properties` include all score columns
- **AND** coordinates are rounded to 6 decimal places

#### Scenario: Large dataset export streams data

- **GIVEN** a dataset with 1M rows
- **WHEN** the user exports to CSV
- **THEN** data is written in chunks (e.g., 10K rows at a time)
- **AND** memory usage remains < 200MB during export

### Requirement: Callback Error Handling

UI callbacks SHALL catch exceptions and display user-friendly error messages without crashing the app.

#### Scenario: Invalid filter value shows error toast

- **GIVEN** a user enters an invalid score range "abc-xyz"
- **WHEN** the filter callback executes
- **THEN** a ValueError is caught
- **AND** an error toast displays: "Invalid score range format"
- **AND** the app remains functional

#### Scenario: Data load failure preserves previous state

- **GIVEN** a valid dataset is currently loaded
- **WHEN** the user attempts to load a corrupted dataset
- **THEN** the load fails with a clear error message
- **AND** the previous dataset remains loaded and functional

### Requirement: Coverage Thresholds by Module

UI module test coverage SHALL meet or exceed the following thresholds:

- `ui/hex_selection.py`: ≥90% line coverage
- `ui/hexes.py`: ≥85% line coverage
- `ui/data_loader.py`: ≥90% line coverage
- `ui/layers.py`: ≥85% line coverage
- `ui/callbacks.py`: ≥85% line coverage
- `ui/__init__.py`: ≥80% line coverage
- `ui/run.py`: ≥70% line coverage
- `ui/export.py`: ≥90% line coverage
- **Overall `ui` module: ≥90% line coverage**

#### Scenario: Coverage gate fails for UI module regression

- **GIVEN** a pull request modifying `ui/data_loader.py`
- **WHEN** the CI pipeline runs coverage checks
- **AND** the module coverage drops to 75% (below 90% threshold)
- **THEN** the coverage gate fails
- **AND** the PR is blocked from merging
