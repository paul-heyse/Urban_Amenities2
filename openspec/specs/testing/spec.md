# Testing Specification

## Purpose

Define the testing standards, coverage targets, and continuous integration expectations for the platform.
## Requirements
### Requirement: Unit Test Coverage

The system SHALL maintain comprehensive unit test coverage for all core functionality.

#### Scenario: Overall coverage reaches 95%+
- **WHEN** running `pytest --cov=src` with the project coverage configuration
- **THEN** the combined line coverage SHALL be at least 95%
- **AND** the test run SHALL fail if coverage drops below that threshold

#### Scenario: Core math modules achieve 90%+ coverage
- **WHEN** running `pytest --cov=src/Urban_Amenities2/math`
- **THEN** coverage SHALL be at least 90% for logsum, gtc, ces, satiation, and diversity modules

#### Scenario: Routing stack achieves 85%+ coverage
- **WHEN** running `pytest --cov=src/Urban_Amenities2/router`
- **THEN** coverage SHALL be at least 85% across API, OSRM, OTP, and CLI helpers with external calls mocked

#### Scenario: UI platform achieves 85%+ coverage
- **WHEN** running `pytest --cov=src/Urban_Amenities2/ui`
- **THEN** coverage SHALL be at least 85% across data loaders, callbacks, layouts, and export utilities

#### Scenario: I/O modules achieve 75%+ coverage
- **WHEN** running `pytest --cov=src/Urban_Amenities2/io`
- **THEN** coverage SHALL be at least 75% for all data ingestion modules
- **AND** external services SHALL be mocked (no real API calls in tests)

#### Scenario: All tests pass under the coverage gate
- **WHEN** running `pytest -q --tb=short`
- **THEN** all tests SHALL pass with exit code 0
- **AND** no import errors SHALL occur
- **AND** the run SHALL respect the coverage thresholds defined above

### Requirement: Property-Based Testing

The system SHALL use property-based testing to validate mathematical invariants.

#### Scenario: Accessibility is monotonic

- **WHEN** generating random inputs with Hypothesis
- **THEN** reducing travel time SHALL NOT decrease accessibility scores
- **AND** adding amenities SHALL NOT decrease scores

#### Scenario: Logsums are homogeneous

- **WHEN** scaling all utilities by constant factor k
- **THEN** logsum SHALL scale by k

#### Scenario: Scores are bounded

- **WHEN** computing any subscore or AUCS total
- **THEN** scores SHALL be in range [0, 100]
- **AND** no NaN or Inf values SHALL occur

---

### Requirement: Integration Testing

The system SHALL provide end-to-end integration tests using realistic data.

#### Scenario: Full pipeline runs on test dataset

- **WHEN** running pipeline on 100-hex test region
- **THEN** pipeline SHALL complete without errors
- **AND** output SHALL pass schema validation
- **AND** all subscores SHALL be computed

#### Scenario: Pipeline is reproducible

- **WHEN** running pipeline twice with same inputs and parameters
- **THEN** outputs SHALL be identical (bit-for-bit)
- **AND** parameter hash SHALL match

#### Scenario: Schema contracts are enforced

- **WHEN** any pipeline stage produces output
- **THEN** output SHALL pass Pandera schema validation
- **AND** violations SHALL cause immediate failure with clear error message

---

### Requirement: External Service Testing

The system SHALL validate integration with external routing services.

#### Scenario: OSRM service is mocked in unit tests

- **WHEN** running unit tests for routing modules
- **THEN** OSRM HTTP calls SHALL be mocked (no real service required)
- **AND** tests SHALL cover success, failure, and timeout scenarios

#### Scenario: OTP service is mocked in unit tests

- **WHEN** running unit tests for transit routing
- **THEN** OTP GraphQL calls SHALL be mocked
- **AND** tests SHALL validate query construction and response parsing

#### Scenario: Service health checks are tested

- **WHEN** testing routing client initialization
- **THEN** health check SHALL detect unreachable services
- **AND** appropriate errors SHALL be raised with actionable messages

---

### Requirement: Data Quality Testing

The system SHALL validate data quality at each pipeline stage.

#### Scenario: Overture data passes schema validation

- **WHEN** ingesting Overture Places or Transportation
- **THEN** data SHALL conform to expected schema (columns, types, ranges)
- **AND** violations SHALL be logged with row details

#### Scenario: GTFS feeds are validated

- **WHEN** loading GTFS static feeds
- **THEN** feeds SHALL be checked with gtfs-kit
- **AND** invalid feeds SHALL be rejected with validation report

#### Scenario: Output quality metrics are computed

- **WHEN** pipeline completes
- **THEN** QA report SHALL include: coverage (% hexes with scores), distribution statistics, anomaly detection
- **AND** QA failures SHALL trigger alerts

---

### Requirement: Test Isolation

The system SHALL ensure tests are independent and can run in any order.

#### Scenario: Tests use temporary directories

- **WHEN** tests write files
- **THEN** each test SHALL use isolated temp directory (pytest tmpdir)
- **AND** temp files SHALL be cleaned up after test

#### Scenario: Tests do not depend on external state

- **WHEN** running tests
- **THEN** tests SHALL NOT require specific files in workspace
- **AND** tests SHALL NOT depend on test execution order

#### Scenario: Tests clean up resources

- **WHEN** tests use resources (files, network connections, processes)
- **THEN** resources SHALL be released in test teardown
- **AND** no leaked resources SHALL remain after test suite

---

### Requirement: Continuous Integration

The system SHALL run tests automatically on code changes.

#### Scenario: Tests run on every commit

- **WHEN** code is pushed to git repository
- **THEN** CI pipeline SHALL run full test suite
- **AND** failures SHALL block merge

#### Scenario: Coverage is tracked over time

- **WHEN** tests run in CI
- **THEN** coverage metrics SHALL be uploaded to Codecov or similar
- **AND** coverage SHALL NOT decrease without justification

#### Scenario: Test results are reported

- **WHEN** tests complete in CI
- **THEN** results SHALL be posted to PR/commit
- **AND** failures SHALL include logs and traceback

### Requirement: Math & Scoring Coverage
Core mathematical kernels and scoring pipelines SHALL maintain deterministic regression tests and property-based checks to sustain the 90% math coverage target.

#### Scenario: CES/logsum regression tests
- **WHEN** running `pytest tests/test_math.py`
- **THEN** tests SHALL cover dtype coercion, rho edge cases, empty inputs, and property-based invariants (monotonicity, homogeneity, bounded outputs)

#### Scenario: Scoring pipeline coverage
- **WHEN** running `pytest tests/test_scores.py`
- **THEN** essentials access, category aggregation, normalisation, and penalty modules SHALL be exercised with deterministic fixtures and snapshot assertions

#### Scenario: Regression guardrails for numba kernels
- **WHEN** executing math/scoring tests under coverage
- **THEN** the numba-compiled paths SHALL be invoked and SHALL guard against regressions such as `'Function' object has no attribute 'dtype'`

### Requirement: Property-Based Mathematical Testing

Mathematical functions SHALL be tested with property-based tests using Hypothesis to verify invariants across the input space.

#### Scenario: CES monotonicity property

- **GIVEN** a CES aggregation function with elasticity ρ
- **WHEN** all inputs are scaled by factor k > 1
- **THEN** the output increases by at least factor k^(1/ρ)
- **AND** the property holds for 100+ randomly generated input vectors

#### Scenario: Satiation monotonicity property

- **GIVEN** a satiation weight function w(n, λ)
- **WHEN** the amenity count n increases
- **THEN** the weight w(n, λ) strictly decreases
- **AND** the property holds for all λ ∈ [0.01, 10] and n ∈ [1, 1000]

### Requirement: Edge Case Coverage

Mathematical functions SHALL explicitly test edge cases including zero inputs, extreme values, and boundary conditions.

#### Scenario: CES with zero inputs

- **GIVEN** a CES aggregation with inputs = [0, 0, 0]
- **WHEN** the function is evaluated
- **THEN** it returns 0.0 without raising an exception

#### Scenario: CES with single non-zero input

- **GIVEN** a CES aggregation with inputs = [42.0, 0, 0]
- **WHEN** the function is evaluated with ρ = 2
- **THEN** it returns 42.0 (single input dominates)

#### Scenario: Satiation with n = 0

- **GIVEN** a satiation weight function with n = 0
- **WHEN** the function is evaluated
- **THEN** it raises `ValueError` with message "n must be positive"

#### Scenario: Satiation large n asymptote

- **GIVEN** a satiation weight function with n = 10^6 and λ = 1.0
- **WHEN** the function is evaluated
- **THEN** the result is < 1e-10 (effectively zero)

### Requirement: Numerical Stability Testing

Mathematical functions SHALL handle extreme values without overflow, underflow, or precision loss.

#### Scenario: CES overflow prevention

- **GIVEN** a CES aggregation with inputs = [1e300, 1e300]
- **WHEN** the function is evaluated with ρ = 2
- **THEN** it returns a finite value without raising `OverflowError`
- **AND** uses stable computation (e.g., scaling before exponentiation)

#### Scenario: Logsum exp overflow protection

- **GIVEN** a logsum with utilities = [1000, 1001, 1002]
- **WHEN** the function is evaluated
- **THEN** it uses the log-sum-exp trick to prevent overflow
- **AND** returns a finite value ≈ 1002 + log(1 + exp(-1) + exp(-2))

#### Scenario: Satiation underflow handling

- **GIVEN** a satiation weight with n = 1000 and λ = 10.0
- **WHEN** exp(-λ*n) underflows to 0.0
- **THEN** the function gracefully handles the underflow
- **AND** returns w(n) ≈ 0.0 without warnings

### Requirement: Regression Test Vectors

Mathematical functions SHALL maintain regression test vectors from production runs to detect unintended behavior changes.

#### Scenario: CES regression vector validated

- **GIVEN** a known CES input: [10.0, 20.0, 30.0] with ρ = 2.0
- **WHEN** the function is evaluated
- **THEN** it returns 22.803508502 ± 1e-6 (relative tolerance)
- **AND** the test fails if the result differs beyond tolerance

#### Scenario: Satiation regression vector validated

- **GIVEN** a known satiation input: n = 5, λ = 0.5
- **WHEN** the function is evaluated
- **THEN** it returns 0.164023457 ± 1e-6
- **AND** the test documents the expected behavior

### Requirement: Elasticity Parameter Coverage

CES aggregation tests SHALL cover the full range of elasticity parameter ρ including limiting cases.

#### Scenario: Cobb-Douglas limit (ρ → 0)

- **GIVEN** a CES aggregation with ρ = 1e-6 (approximating 0)
- **WHEN** the function is evaluated with inputs = [2, 8]
- **THEN** it returns approximately geometric mean: sqrt(2 * 8) = 4.0
- **AND** the result is within 1% of true Cobb-Douglas formula

#### Scenario: Linear aggregation (ρ = 1)

- **GIVEN** a CES aggregation with ρ = 1.0
- **WHEN** the function is evaluated with inputs = [10, 20, 30]
- **THEN** it returns exactly the arithmetic mean: 20.0

#### Scenario: Complementary goods (ρ < 0)

- **GIVEN** a CES aggregation with ρ = -1.0
- **WHEN** the function is evaluated with inputs = [10, 20]
- **THEN** the result is less than min(inputs) = 10
- **AND** reflects strong complementarity (lack of one input hurts total)

#### Scenario: Near-perfect substitutes (ρ = 10)

- **GIVEN** a CES aggregation with ρ = 10.0
- **WHEN** the function is evaluated with inputs = [5, 10, 15]
- **THEN** the result is approximately max(inputs) = 15
- **AND** within 1% of the maximum input

### Requirement: Diversity Metric Testing

Diversity bonus calculations SHALL test uniform, skewed, and degenerate category distributions.

#### Scenario: Uniform distribution maximizes diversity

- **GIVEN** category counts = [10, 10, 10, 10]
- **WHEN** the diversity metric is calculated
- **THEN** it returns the maximum value (1.0 for normalized metrics)

#### Scenario: Skewed distribution reduces diversity

- **GIVEN** category counts = [100, 1, 1, 1]
- **WHEN** the diversity metric is calculated
- **THEN** it returns a value < 0.5 (concentrated distribution)

#### Scenario: Single category has zero diversity

- **GIVEN** category counts = [50]
- **WHEN** the diversity metric is calculated
- **THEN** it returns 0.0 (no diversity)

#### Scenario: Zero-count categories excluded

- **GIVEN** category counts = [10, 0, 0, 5]
- **WHEN** the diversity metric is calculated
- **THEN** only non-zero categories [10, 5] are included
- **AND** zero counts are ignored (not treated as present categories)

### Requirement: Vectorized Operation Testing

Mathematical functions that support array inputs SHALL test vectorized operations for correctness and performance.

#### Scenario: Satiation vectorized over amenity counts

- **GIVEN** an array of amenity counts n = [1, 2, 5, 10]
- **WHEN** the satiation weight function is applied
- **THEN** it returns element-wise results: [w(1), w(2), w(5), w(10)]
- **AND** the vectorized result matches individual evaluations

#### Scenario: CES vectorized over multiple locations

- **GIVEN** a 2D array of inputs (1000 locations × 5 amenity types)
- **WHEN** CES aggregation is applied row-wise
- **THEN** it returns 1000 aggregated scores
- **AND** completes in < 100ms (vectorization performance requirement)

### Requirement: Coverage Thresholds by Module

Math module test coverage SHALL meet or exceed the following thresholds:

- `math/ces.py`: ≥95% line coverage
- `math/satiation.py`: ≥95% line coverage
- `math/diversity.py`: ≥95% line coverage
- `math/logsum.py`: ≥98% line coverage
- `math/gtc.py`: ≥100% line coverage (maintain existing)
- **Overall `math` module: ≥95% line coverage**

#### Scenario: Coverage gate fails for math module regression

- **GIVEN** a pull request modifying `math/satiation.py`
- **WHEN** the CI pipeline runs coverage checks
- **AND** the module coverage drops to 80% (below 95% threshold)
- **THEN** the coverage gate fails
- **AND** the PR is blocked from merging

### Requirement: Floating-Point Precision Documentation

Tests SHALL document expected floating-point precision using relative tolerance (rtol) in assertions.

#### Scenario: CES test uses appropriate tolerance

- **GIVEN** a CES aggregation test with expected result 22.803508502
- **WHEN** the assertion is written
- **THEN** it uses `pytest.approx(expected, rel=1e-6)` for 6 decimal places
- **AND** the tolerance is documented as appropriate for typical inputs

#### Scenario: Satiation test uses stricter tolerance

- **GIVEN** a satiation weight test with small expected result 1e-5
- **WHEN** the assertion is written
- **THEN** it uses `pytest.approx(expected, rel=1e-4, abs=1e-10)` with absolute tolerance
- **AND** handles cases where relative tolerance alone is insufficient

### Requirement: UI Regression Coverage
The UI platform SHALL provide regression tests that exercise data loading, layout rendering, and export flows to sustain the 85% coverage target.

#### Scenario: DataContext regression suite
- **WHEN** running `pytest tests/test_ui_data_loader.py`
- **THEN** tests SHALL cover dataset discovery, metadata joins, overlay construction (with and without shapely), and error logging paths
- **AND** failures SHALL block the build

#### Scenario: Layout and callback coverage
- **WHEN** running `pytest tests/test_ui_layouts.py`
- **THEN** Dash layouts and callbacks SHALL be executed to validate component registration, overlay payloads, and export callbacks without raising exceptions

#### Scenario: UI helper coverage
- **WHEN** running `pytest tests/test_ui_components_structure.py tests/test_ui_export.py`
- **THEN** utility helpers (`ui.performance`, `ui.downloads`, `ui.layers`, export builders) SHALL have deterministic tests that verify their outputs and increase coverage for the UI package

### Requirement: Routing Regression Coverage
Routing clients, APIs, and CLI commands SHALL be covered by deterministic tests to sustain the 85% routing coverage target.

#### Scenario: OSRM client coverage
- **WHEN** running `pytest tests/test_routing.py -k osrm`
- **THEN** tests SHALL assert route batching, table concatenation, and error handling for OSRM responses (including dict and dataclass payloads)
- **AND** no external HTTP requests SHALL be made

#### Scenario: RoutingAPI matrix coverage
- **WHEN** running `pytest tests/test_routing.py -k matrix`
- **THEN** `RoutingAPI.matrix` SHALL be exercised for car and transit modes, covering duration-only tables, missing distances, and cache hits

#### Scenario: CLI routing coverage
- **WHEN** running `pytest tests/test_cli.py -k routing`
- **THEN** the `routing compute-skims` command SHALL be tested end-to-end with temporary CSV inputs and exported Parquet outputs, ensuring coverage reflects the CLI workflow

