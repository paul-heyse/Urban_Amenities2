## MODIFIED Requirements

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
