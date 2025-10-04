# Implementation Tasks: Add CLI and Configuration Module Test Coverage

## 1. Test Infrastructure Setup

- [x] 1.1 Create `tests/cli/` and `tests/config/` directories
- [x] 1.2 Create `tests/fixtures/configs/` for sample configuration files
- [x] 1.3 Define shared CLI fixtures in `tests/cli/conftest.py`
- [x] 1.4 Define shared config fixtures in `tests/config/conftest.py`

## 2. CLI Command Testing (High Priority)

- [x] 2.1 Create `tests/cli/test_ingest_command.py`
  - [x] Test `ingest overture-places --output data/places.parquet`:
    - [x] Valid execution with mocked BigQuery
    - [x] Output file created
    - [ ] Schema validation passes
  - [x] Test `ingest gtfs --feed-url URL --output data/gtfs/`:
    - [x] GTFS feed downloaded
    - [x] Static GTFS files extracted
    - [ ] Validation passes
  - [ ] Test `ingest noaa-climate --stations CO --output data/climate.parquet`:
    - [ ] Station data fetched
    - [ ] Monthly normals parsed
    - [ ] Output written
  - [ ] Test error handling:
    - [x] Invalid source type → clear error message
    - [x] Missing required argument → usage displayed
    - [ ] Network error → retry logic triggered

- [ ] 2.2 Create `tests/cli/test_score_command.py`
  - [ ] Test `score essentials --input data/places.parquet --params config.yaml --output scores/ea.parquet`:
    - [ ] Config loaded correctly
    - [ ] EA scoring executed
    - [ ] Output file created with expected schema
  - [ ] Test all subscores (EA, LCA, MUHAA, JEA, MORR, CTE, SOU)
  - [ ] Test parameter file validation:
    - [ ] Missing parameter → error with specific parameter name
    - [ ] Invalid parameter type → type error message
  - [ ] Test input data validation:
    - [ ] Missing required column → schema error
    - [ ] Empty DataFrame → warning, no output
  - [ ] Test progress reporting:
    - [ ] Progress bar updates during scoring
    - [ ] Final summary displayed

- [x] 2.3 Create `tests/cli/test_aggregate_command.py`
  - [x] Test `aggregate --input scores/ --params config.yaml --output aucs.parquet`:
    - [x] All subscore files loaded
    - [x] Aggregation weights applied
    - [x] Normalization executed
    - [x] Output written
  - [ ] Test export formats:
    - [ ] `--format parquet` → `.parquet` file
    - [ ] `--format csv` → `.csv` file
    - [ ] `--format geojson` → `.geojson` file (with geometries)
  - [ ] Test error handling:
    - [x] Missing subscore files → error listing missing files
    - [ ] Incompatible hex_id sets → merge error

- [ ] 2.4 Create `tests/cli/test_ui_command.py`
  - [ ] Test `ui --data-path data/ --port 8050`:
    - [ ] Server starts (mock, don't actually bind port)
    - [ ] Data path validated
    - [ ] Port number valid
  - [ ] Test `ui --help`:
    - [ ] Help text includes all options
    - [ ] Examples provided

- [ ] 2.5 Create `tests/cli/test_validate_command.py`
  - [ ] Test `validate --input data/places.parquet --schema overture_places`:
    - [ ] Schema validation executed
    - [ ] Validation report displayed
    - [ ] Exit code 0 for valid, non-zero for invalid
  - [ ] Test validation error reporting:
    - [ ] Column type mismatch → clear error
    - [ ] Missing column → column name in error
    - [ ] Outlier detected → row number and value in error

## 3. CLI Error Handling Testing

- [x] 3.1 Create `tests/cli/test_cli_errors.py`
  - [x] Test missing required arguments:
    - [x] `score essentials` (missing --input) → usage displayed
    - [x] Exit code non-zero
  - [x] Test invalid file paths:
    - [x] `score essentials --input nonexistent.parquet` → file not found error
    - [x] Clear error message with path
  - [ ] Test conflicting options:
    - [ ] `aggregate --input scores/ --format csv --output file.parquet` → extension mismatch warning
  - [ ] Test keyboard interrupt handling:
    - [ ] Simulate Ctrl+C during long operation → graceful shutdown

## 4. Configuration Loader Testing (High Priority)

- [x] 4.1 Create `tests/config/test_loader.py`
  - [x] Test loading valid YAML:

    ```yaml
    # tests/fixtures/configs/valid.yaml
    accessibility:
      vot_weekday: 18.0
      vot_weekend: 15.0
    scoring:
      ea_threshold: 30.0
    ```

    - [x] All parameters parsed
    - [x] Types correct (float, int, etc.)
- [x] Test malformed YAML:
    - [x] Invalid syntax → `yaml.YAMLError` with line number
    - [x] Tab/space mixing → parsing error
  - [x] Test missing required sections:
    - [x] Config without `scoring` section → error
    - [x] Clear message: "Required section 'scoring' missing"
  - [ ] Test unknown parameters (strict mode):
    - [x] Extra param `unknown_param` → validation error
    - [ ] Warning mode: log warning, ignore parameter

- [x] 4.2 Test parameter merging:

  ```python
  base_config = load_config("base.yaml")
  override_config = load_config("override.yaml")
  merged = merge_configs(base_config, override_config)
  assert merged.accessibility.vot_weekday == override_value
  ```

  - [x] Override values replace base values
  - [ ] Non-overridden values preserved from base
  - [ ] Nested dict merging works correctly

- [x] 4.3 Test environment variable overrides:

  ```bash
  export AUCS_VOT_WEEKDAY=20.0
  ```

  - [x] Env var overrides config file
  - [x] Precedence: env var > override file > base file > defaults

- [ ] 4.4 Test configuration validation:
  - [ ] Type checking:
    - [ ] `vot_weekday: "not_a_number"` → type error
  - [ ] Range validation:
    - [ ] `vot_weekday: -5.0` → range error (must be positive)
  - [ ] Required parameter enforcement:
    - [ ] Missing `vot_weekday` → error

- [ ] 4.5 Test configuration caching:
  - [ ] Load config, verify hash generated
  - [ ] Load same config again → cached version returned
  - [ ] Modify config file → cache invalidated, reloaded

- [ ] 4.6 Test default configuration:
  - [ ] Load config with missing optional params
  - [ ] Defaults applied for missing params
  - [ ] Warning logged for deprecated params

## 5. Parameter Models Testing (High Priority)

- [ ] 5.1 Create `tests/config/test_params.py`
  - [ ] Test `AccessibilityParams` model:
    - [ ] Valid parameters → model instantiated
    - [ ] Invalid type (`vot_weekday="abc"`) → `ValidationError`
    - [ ] Out-of-range (`vot_weekday=-5`) → `ValidationError`
  - [ ] Test `ScoringParams` model:
    - [ ] All subscores parameters validated
    - [ ] Nested structures (e.g., `ea.categories`) parsed correctly
  - [ ] Test cross-field validation:

    ```python
    class RangeParams(BaseModel):
        min_value: float
        max_value: float

        @validator('max_value')
        def max_greater_than_min(cls, v, values):
            if 'min_value' in values and v <= values['min_value']:
                raise ValueError('max_value must be > min_value')
            return v
    ```

    - [ ] `min_value=10, max_value=5` → validation error
  - [ ] Test custom validators:
    - [ ] Enum validation (e.g., `mode` must be in ["walk", "bike", "transit", "car"])
    - [ ] List length validation
    - [ ] Regex validation for strings

- [ ] 5.2 Test parameter serialization:
  - [ ] To YAML:

    ```python
    params = AccessibilityParams(vot_weekday=18.0, ...)
    yaml_str = params.to_yaml()
    assert "vot_weekday: 18.0" in yaml_str
    ```

  - [x] To JSON:

    ```python
    json_dict = params.dict()
    assert json_dict["vot_weekday"] == 18.0
    ```

  - [x] Round-trip:

    ```python
    params1 = AccessibilityParams(...)
    yaml_str = params1.to_yaml()
    params2 = AccessibilityParams.from_yaml(yaml_str)
    assert params1 == params2
    ```

- [ ] 5.3 Test parameter defaults:
  - [x] All optional parameters have defaults
  - [ ] Defaults match documented values in specs
  - [ ] Defaults produce sensible scores (smoke test)

- [ ] 5.4 Test parameter versioning:
  - [ ] Version field populated in all models
  - [ ] Hash generation for reproducibility:

    ```python
    params = AccessibilityParams(...)
    hash1 = params.compute_hash()
    # Modify param
    params.vot_weekday = 20.0
    hash2 = params.compute_hash()
    assert hash1 != hash2
    ```

## 6. Golden Configuration Files

- [ ] 6.1 Create golden config files in `tests/fixtures/configs/`:
  - [x] `golden_v1.yaml` - Full config with all parameters (version 1.0)
  - [x] `golden_v2.yaml` - Updated config (version 2.0)
  - [x] `minimal.yaml` - Minimal valid config
  - [x] `invalid_type.yaml` - Config with type error
  - [ ] `invalid_range.yaml` - Config with out-of-range value
  - [ ] `missing_required.yaml` - Config missing required section

- [x] 6.2 Test golden configs:

  ```python
  def test_golden_v1_loads_correctly():
      params = load_config("tests/fixtures/configs/golden_v1.yaml")
      assert params.accessibility.vot_weekday == 18.0
      assert params.scoring.ea.threshold == 30.0
      # ... test all expected values
  ```

## 7. CLI Integration Testing

- [ ] 7.1 Create `tests/cli/test_cli_integration.py`
  - [ ] Test full pipeline:

    ```bash
    # Step 1: Ingest
    cli ingest overture-places --output /tmp/places.parquet
    # Step 2: Score
    cli score essentials --input /tmp/places.parquet --output /tmp/ea.parquet
    # Step 3: Aggregate
    cli aggregate --input /tmp/ --output /tmp/aucs.parquet
    # Verify final output
    assert Path("/tmp/aucs.parquet").exists()
    df = pd.read_parquet("/tmp/aucs.parquet")
    assert "aucs" in df.columns
    ```

  - [ ] Test error propagation:
    - [ ] If `ingest` fails, `score` should not run
    - [ ] If `score` produces invalid output, `aggregate` should error

## 8. CLI Help and Documentation Testing

- [ ] 8.1 Create `tests/cli/test_cli_help.py`
  - [x] Test `cli --help`:
    - [x] Help text displayed
    - [x] All commands listed
  - [x] Test `cli score --help`:
    - [x] Command description
    - [x] All options listed
    - [ ] Examples provided

## 9. Configuration Utilities Testing

- [ ] 9.1 Create `tests/config/test_config_utils.py`
  - [ ] Test parameter search by name:

    ```python
    results = search_parameters("vot")
    assert "vot_weekday" in results
    assert "vot_weekend" in results
    ```

  - [ ] Test configuration diff:

    ```python
    config1 = load_config("v1.yaml")
    config2 = load_config("v2.yaml")
    diff = config_diff(config1, config2)
    assert diff.changed == ["vot_weekday"]
    assert diff.added == ["new_param"]
    assert diff.removed == ["deprecated_param"]
    ```

## 10. Verification & Coverage Check

- [ ] 10.1 Run CLI tests: `pytest tests/cli/ -v --cov=src/Urban_Amenities2/cli --cov-report=term-missing`
- [ ] 10.2 Run config tests: `pytest tests/config/ -v --cov=src/Urban_Amenities2/config --cov-report=term-missing`
- [ ] 10.3 Verify targets:
  - [ ] `cli/main.py`: ≥85%
  - [ ] `config/loader.py`: ≥90%
  - [ ] `config/params.py`: ≥95%
- [ ] 10.4 Verify overall `cli` + `config` coverage ≥90%
