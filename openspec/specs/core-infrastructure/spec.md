# core-infrastructure Specification

## Purpose
TBD - created by archiving change add-core-infrastructure. Update Purpose after archive.
## Requirements
### Requirement: Data Schema Validation

The system SHALL validate all intermediate data tables against defined Pandera schemas.

#### Scenario: Validate POI schema

- **WHEN** POI data is loaded or transformed
- **THEN** the system SHALL check that poi_id, hex_id, aucstype, lat, lon are present and valid

#### Scenario: Catch invalid travel times

- **WHEN** travel time skims are computed
- **THEN** the system SHALL reject negative durations or missing required fields

#### Scenario: Validation failure reporting

- **WHEN** schema validation fails
- **THEN** the system SHALL report specific rows and columns with violations

### Requirement: Run Reproducibility Tracking

The system SHALL track all inputs and parameters for each scoring run to ensure reproducibility.

#### Scenario: Create run manifest

- **WHEN** a scoring run begins
- **THEN** the system SHALL generate a unique run_id and record parameter hash, data snapshot IDs, timestamp, and git commit

#### Scenario: Retrieve historical run details

- **WHEN** a user queries a past run by run_id
- **THEN** the system SHALL display the complete parameter configuration and data versions used

#### Scenario: Reproduce past runs

- **WHEN** the same parameters and data snapshots are provided
- **THEN** the system SHALL produce identical output scores (within numerical precision)

### Requirement: Data Snapshot Management

The system SHALL track versions of all external data sources.

#### Scenario: Register data snapshot

- **WHEN** external data (Overture, GTFS, LODES) is downloaded
- **THEN** the system SHALL record source name, version/release date, download timestamp, and file hash

#### Scenario: Detect stale data

- **WHEN** data snapshots are older than configured thresholds
- **THEN** the system SHALL warn users about potentially outdated inputs

### Requirement: Structured Logging

The system SHALL emit structured JSON logs for all pipeline stages and computations.

#### Scenario: Log stage completion

- **WHEN** a pipeline stage (e.g., "travel_time_computation") completes
- **THEN** logs SHALL include run_id, stage_name, duration_seconds, input_row_count, output_row_count, status

#### Scenario: Log warnings and errors

- **WHEN** non-fatal issues occur (e.g., missing optional data)
- **THEN** logs SHALL capture context (hex_id, poi_id, mode) for debugging

#### Scenario: Performance monitoring

- **WHEN** operations exceed expected duration
- **THEN** logs SHALL include timing information for performance analysis

### Requirement: Command-Line Interface

The system SHALL provide a CLI for all major operations and utilities.

#### Scenario: Validate configuration

- **WHEN** a user runs `aucs config validate configs/params.yml`
- **THEN** the system SHALL check the YAML, report any errors, and exit with appropriate code

#### Scenario: Display hex information

- **WHEN** a user runs `aucs hex info 39.7392 -104.9903`
- **THEN** the system SHALL display the H3 cell ID, neighbors, and summary statistics for that location

#### Scenario: Initialize scoring run

- **WHEN** a user runs `aucs run init --params configs/params.yml`
- **THEN** the system SHALL create a run manifest, validate parameters, and prepare output directories

### Requirement: Error Classification and Handling

The system SHALL classify errors into categories and handle them appropriately.

#### Scenario: Data quality errors

- **WHEN** input data has quality issues (duplicates, missing required fields)
- **THEN** the system SHALL log warnings, apply configured fallbacks, and continue processing

#### Scenario: Configuration errors

- **WHEN** invalid parameters are detected
- **THEN** the system SHALL fail fast with clear error messages before computations begin

#### Scenario: Computation errors

- **WHEN** mathematical operations fail (e.g., division by zero, overflow)
- **THEN** the system SHALL catch exceptions, log context, and provide fallback values or skip affected records

