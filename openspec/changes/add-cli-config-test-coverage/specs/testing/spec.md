# Spec Delta: CLI and Configuration Testing Requirements

## ADDED Requirements

### Requirement: CLI Command Testing

CLI commands SHALL be tested using `typer.testing.CliRunner` with mocked external dependencies.

#### Scenario: Ingest command executes successfully

- **GIVEN** a mock BigQuery client returning sample POI data
- **WHEN** the CLI command `ingest overture-places --output /tmp/places.parquet` is invoked
- **THEN** the command exits with code 0
- **AND** the output file `/tmp/places.parquet` is created
- **AND** the file contains the expected schema

#### Scenario: Score command validates input data

- **GIVEN** an input file with missing required column `hex_id`
- **WHEN** the CLI command `score essentials --input bad_data.parquet` is invoked
- **THEN** the command exits with non-zero code
- **AND** the error message identifies the missing column
- **AND** no output file is created

### Requirement: CLI Error Handling

CLI SHALL provide clear error messages for invalid arguments, missing files, and runtime errors.

#### Scenario: Missing required argument displays usage

- **GIVEN** the CLI is invoked with `score essentials` (missing --input)
- **WHEN** the command executes
- **THEN** it exits with code 2 (argument error)
- **AND** displays usage: "Error: Missing option '--input'"

#### Scenario: Invalid file path shows clear error

- **GIVEN** the CLI is invoked with `--input /nonexistent/file.parquet`
- **WHEN** the command attempts to load the file
- **THEN** it exits with code 1
- **AND** displays: "Error: File not found: /nonexistent/file.parquet"

#### Scenario: Keyboard interrupt exits gracefully

- **GIVEN** a long-running command is executing
- **WHEN** the user presses Ctrl+C
- **THEN** the command catches KeyboardInterrupt
- **AND** displays: "Operation cancelled by user"
- **AND** cleans up temporary files before exit

### Requirement: Configuration File Loading

Configuration files SHALL be loaded from YAML with full Pydantic validation.

#### Scenario: Valid configuration file loads successfully

- **GIVEN** a YAML file:

  ```yaml
  accessibility:
    vot_weekday: 18.0
  scoring:
    ea_threshold: 30.0
  ```

- **WHEN** the configuration is loaded
- **THEN** a `Params` object is created
- **AND** `params.accessibility.vot_weekday == 18.0`

#### Scenario: Malformed YAML syntax shows error

- **GIVEN** a YAML file with syntax error (e.g., unmatched bracket)
- **WHEN** the configuration loader attempts to parse it
- **THEN** a `yaml.YAMLError` is raised
- **AND** the error message includes the line number

#### Scenario: Missing required section fails validation

- **GIVEN** a YAML file without the `scoring` section
- **WHEN** the configuration is validated
- **THEN** a `ValidationError` is raised
- **AND** the message states: "Required section 'scoring' missing"

### Requirement: Parameter Merging

Configuration loading SHALL support merging base config, override config, and environment variables.

#### Scenario: Override config replaces base values

- **GIVEN** base config with `vot_weekday: 18.0`
- **AND** override config with `vot_weekday: 20.0`
- **WHEN** configs are merged with override taking precedence
- **THEN** the merged config has `vot_weekday: 20.0`

#### Scenario: Environment variable overrides config file

- **GIVEN** config file with `vot_weekday: 18.0`
- **AND** environment variable `AUCS_VOT_WEEKDAY=22.0`
- **WHEN** the configuration is loaded
- **THEN** `params.accessibility.vot_weekday == 22.0`

#### Scenario: Precedence order enforced

- **GIVEN** multiple sources for `vot_weekday`:
  - Default: 15.0
  - Base config: 18.0
  - Override config: 20.0
  - Environment variable: 22.0
- **WHEN** all sources are merged
- **THEN** the final value is 22.0 (env var wins)

### Requirement: Parameter Validation

Configuration parameters SHALL be validated for type, range, and cross-field constraints.

#### Scenario: Type validation catches string for numeric field

- **GIVEN** a config with `vot_weekday: "not_a_number"`
- **WHEN** the Pydantic model is instantiated
- **THEN** a `ValidationError` is raised
- **AND** the message states: "vot_weekday must be a number"

#### Scenario: Range validation enforces minimum

- **GIVEN** a config with `vot_weekday: -5.0`
- **AND** a validator requiring `vot_weekday > 0`
- **WHEN** the model is validated
- **THEN** a `ValidationError` is raised
- **AND** the message states: "vot_weekday must be positive"

#### Scenario: Cross-field validation enforces constraints

- **GIVEN** a config with `min_score: 50.0` and `max_score: 30.0`
- **AND** a validator requiring `max_score > min_score`
- **WHEN** the model is validated
- **THEN** a `ValidationError` is raised
- **AND** the message states: "max_score must be greater than min_score"

### Requirement: Configuration Caching

Loaded configurations SHALL be cached with hash-based versioning for reproducibility.

#### Scenario: Configuration hash generated on load

- **GIVEN** a configuration is loaded from `config.yaml`
- **WHEN** the hash is computed
- **THEN** a deterministic hash string is generated
- **AND** the hash changes if any parameter value changes

#### Scenario: Cache hit returns cached config

- **GIVEN** a configuration has been loaded and cached
- **WHEN** the same file is loaded again
- **AND** the file has not been modified
- **THEN** the cached configuration is returned
- **AND** the YAML file is not re-parsed

#### Scenario: Cache invalidation on file modification

- **GIVEN** a configuration is cached
- **WHEN** the config file is modified
- **THEN** the cache detects the modification (mtime check)
- **AND** the file is reloaded and re-validated

### Requirement: Parameter Defaults

Configuration parameters SHALL provide sensible defaults for all optional fields.

#### Scenario: Optional parameter missing uses default

- **GIVEN** a config file without `transit_wait_penalty`
- **WHEN** the configuration is loaded
- **THEN** `params.accessibility.transit_wait_penalty == 2.0` (default)

#### Scenario: Defaults match documented values

- **GIVEN** the parameter specification states `vot_weekday` default is 18.0
- **WHEN** a config without `vot_weekday` is loaded
- **THEN** `params.accessibility.vot_weekday == 18.0`

### Requirement: Parameter Serialization

Configuration SHALL support round-trip serialization to YAML and JSON.

#### Scenario: Params to YAML serialization

- **GIVEN** a `Params` object with all fields populated
- **WHEN** `params.to_yaml()` is called
- **THEN** a valid YAML string is returned
- **AND** the YAML can be parsed back to an equivalent `Params` object

#### Scenario: Params to JSON serialization

- **GIVEN** a `Params` object
- **WHEN** `params.dict()` is called
- **THEN** a JSON-serializable dict is returned
- **AND** all nested structures are preserved

#### Scenario: Round-trip preserves values

- **GIVEN** a `Params` object with specific values
- **WHEN** serialized to YAML and deserialized back
- **THEN** the deserialized object is equal to the original
- **AND** all parameter values match exactly

### Requirement: CLI Integration Testing

CLI workflows SHALL be tested end-to-end with realistic data and configurations.

#### Scenario: Full pipeline executes successfully

- **GIVEN** mock data sources (POIs, GTFS, climate, etc.)
- **WHEN** the pipeline is executed:
  1. `ingest overture-places --output /tmp/places.parquet`
  2. `score essentials --input /tmp/places.parquet --output /tmp/ea.parquet`
  3. `aggregate --input /tmp/ --output /tmp/aucs.parquet`
- **THEN** all commands exit with code 0
- **AND** the final output `/tmp/aucs.parquet` contains expected schema
- **AND** scores are within valid ranges

#### Scenario: Pipeline error stops execution

- **GIVEN** the `ingest` command fails (network error)
- **WHEN** the pipeline script is executed
- **THEN** the `ingest` command exits with non-zero code
- **AND** subsequent `score` command is not executed
- **AND** a clear error message is logged

### Requirement: CLI Help Documentation

CLI commands SHALL provide comprehensive help text with examples.

#### Scenario: Main help lists all commands

- **GIVEN** the CLI is invoked with `--help`
- **WHEN** the help text is displayed
- **THEN** all commands are listed (ingest, score, aggregate, ui, validate)
- **AND** each command has a brief description

#### Scenario: Command help includes examples

- **GIVEN** the CLI is invoked with `score --help`
- **WHEN** the help text is displayed
- **THEN** all options are documented
- **AND** at least one usage example is provided

### Requirement: Configuration Utilities

Configuration management SHALL provide utilities for parameter search and version diffing.

#### Scenario: Parameter search by name

- **GIVEN** a function `search_parameters(query: str)`
- **WHEN** invoked with query "vot"
- **THEN** returns ["vot_weekday", "vot_weekend", ...]
- **AND** all matching parameters are included

#### Scenario: Configuration diff identifies changes

- **GIVEN** two configuration versions (v1 and v2)
- **WHEN** `config_diff(v1, v2)` is called
- **THEN** changed parameters are listed: ["vot_weekday"]
- **AND** added parameters are listed: ["new_param"]
- **AND** removed parameters are listed: ["deprecated_param"]

### Requirement: Coverage Thresholds by Module

CLI and configuration module test coverage SHALL meet or exceed the following thresholds:

- `cli/main.py`: ≥85% line coverage
- `config/loader.py`: ≥90% line coverage
- `config/params.py`: ≥95% line coverage
- **Overall `cli` + `config` modules: ≥90% line coverage**

#### Scenario: Coverage gate fails for CLI regression

- **GIVEN** a pull request modifying `cli/main.py`
- **WHEN** the CI pipeline runs coverage checks
- **AND** the module coverage drops to 70% (below 85% threshold)
- **THEN** the coverage gate fails
- **AND** the PR is blocked from merging
