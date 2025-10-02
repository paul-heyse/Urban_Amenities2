# Testing Specification

## ADDED Requirements

### Requirement: Unit Test Coverage

The system SHALL maintain comprehensive unit test coverage for all core functionality.

#### Scenario: Core math modules achieve 80%+ coverage

- **WHEN** running `pytest --cov=src/Urban_Amenities2/math`
- **THEN** coverage SHALL be at least 80% for logsum, gtc, ces, satiation, diversity modules

#### Scenario: I/O modules achieve 60%+ coverage

- **WHEN** running `pytest --cov=src/Urban_Amenities2/io`
- **THEN** coverage SHALL be at least 60% for all data ingestion modules
- **AND** external services SHALL be mocked (no real API calls in tests)

#### Scenario: All tests pass

- **WHEN** running `pytest -q --tb=short`
- **THEN** all tests SHALL pass with exit code 0
- **AND** no import errors SHALL occur

---

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
