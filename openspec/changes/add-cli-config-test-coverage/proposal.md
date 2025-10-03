# Change Proposal: Add CLI and Configuration Module Test Coverage

## Why

The CLI (`cli/main.py`: 65.85%) and configuration modules (`config/loader.py`: 55.70%, `config/params.py`: 75.16%) have low test coverage, creating risk for:

- CLI command argument parsing errors
- Invalid configuration files silently accepted
- Parameter validation failures leading to incorrect scoring
- Missing required files not detected until runtime

The CLI is the primary interface for batch processing and production pipelines. Configuration modules manage 600+ parameters that directly affect score calculations. Untested code paths in these critical areas can cause:

- Silent failures in automated pipelines
- Incorrect parameter propagation through the scoring system
- Difficult-to-diagnose configuration errors
- Production incidents from malformed config files

## What Changes

### High-Priority Coverage Additions

**CLI Commands (`cli/main.py` - Currently 65.85%):**

- Test `ingest` command:
  - All supported source types (overture, gtfs, noaa, padus, lodes, nces, etc.)
  - Output path validation and creation
  - Error handling for missing input files
  - Progress reporting
- Test `score` command:
  - All subscores (EA, LCA, MUHAA, JEA, MORR, CTE, SOU)
  - Parameter file loading and validation
  - Input data validation
  - Output file generation
- Test `aggregate` command:
  - Aggregation across subscores
  - Normalization parameters
  - Export formats (Parquet, CSV, GeoJSON)
- Test `ui` command:
  - Server startup options
  - Port configuration
  - Data path validation
- Test `validate` command:
  - Schema validation for all data types
  - Error reporting format
- Test CLI error handling:
  - Missing required arguments
  - Invalid file paths
  - Conflicting options
- Test CLI help and documentation:
  - `--help` output format
  - Command descriptions

**Configuration Loader (`config/loader.py` - Currently 55.70%):**

- Test YAML file loading:
  - Valid config files
  - Malformed YAML syntax
  - Missing required sections
  - Unknown parameters (strict mode)
- Test parameter merging:
  - Base config + override config
  - Environment variable overrides
  - CLI argument overrides
  - Precedence order
- Test configuration validation:
  - Type checking (int, float, string, list, dict)
  - Range validation (min/max constraints)
  - Required parameter enforcement
- Test configuration caching:
  - Config hash generation for reproducibility
  - Cache invalidation on file changes
- Test default configuration:
  - Fallback to defaults when optional parameters missing
  - Warning for deprecated parameters

**Parameter Models (`config/params.py` - Currently 75.16%):**

- Test Pydantic model validation:
  - All parameter groups (AccessibilityParams, ScoringParams, etc.)
  - Nested parameter structures
  - Cross-field validation (e.g., min_value < max_value)
  - Custom validators
- Test parameter serialization:
  - To YAML for config export
  - To JSON for API responses
- Test parameter defaults:
  - All optional parameters have sensible defaults
  - Defaults match documented values
- Test parameter versioning:
  - Version field populated
  - Hash generation for reproducibility

### Medium-Priority Coverage Additions

**CLI Utilities:**

- Test progress bar formatting
- Test logging configuration from CLI flags
- Test color output toggling (--no-color)

**Configuration Utilities:**

- Test parameter search by name
- Test parameter documentation generation
- Test configuration diff between versions

### Testing Strategy

**CLI Testing with `typer.testing.CliRunner`:**

- Use `CliRunner().invoke()` for command simulation
- Capture stdout/stderr for assertion
- Test exit codes (0 for success, non-zero for errors)
- Use temporary directories for input/output files

**Configuration Testing:**

- Use `pytest.fixture` for sample config files
- Test with valid and invalid YAML structures
- Use Pydantic's validation errors for assertion
- Test configuration serialization round-trip

**Regression Testing:**

- Maintain golden config files in `tests/fixtures/configs/`
- Test that loading golden configs produces expected parameter values
- Detect breaking changes to config schema

**Integration Testing:**

- Test full CLI workflows:
  - `ingest` → `score` → `aggregate` → `ui`
- Verify intermediate outputs match expectations
- Test error propagation through pipeline stages

### Coverage Targets

- `cli/main.py`: 65.85% → 85%
- `config/loader.py`: 55.70% → 90%
- `config/params.py`: 75.16% → 95%
- **Overall `cli` + `config` modules: 68% → 90%+**

## Impact

**Affected specs:**

- `specs/testing/spec.md` (add CLI and config testing requirements)
- `specs/parameter-management/spec.md` (clarify validation rules)
- `specs/core-infrastructure/spec.md` (document CLI contract)

**Affected code:**

- `src/Urban_Amenities2/cli/` (test additions only)
- `src/Urban_Amenities2/config/` (test additions only)
- New test files in `tests/cli/` and `tests/config/`
- Golden config files in `tests/fixtures/configs/`

**Benefits:**

- Increased confidence in CLI correctness for production pipelines
- Earlier detection of configuration errors
- Protection against parameter schema breaking changes
- Documented expected CLI behavior through tests

**Risks:**

- CLI tests can be slow if invoking full commands (mitigate with unit tests for components)
- Config tests may need updates when parameter schema evolves
- Integration tests may be brittle if intermediate file formats change

**Migration:**

- No production code changes
- Existing tests remain unchanged
- New tests added to expand coverage
