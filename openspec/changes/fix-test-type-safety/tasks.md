# Implementation Tasks: Fix Test Type Safety

## 1. DataFrame Type Narrowing (High Priority)

- [ ] 1.1 **Analyze test_quality.py DataFrame operations** (lines 43-101)
  - [ ] Identify all `.loc[]` comparisons triggering union type explosions
  - [ ] Document actual column dtypes for each DataFrame fixture
  - [ ] Map mypy errors to specific comparison operations

- [ ] 1.2 **Create TypedDataFrame protocols**
  - [ ] Define `POIDataFrame` protocol for quality testing fixtures
  - [ ] Define `ScoredDataFrame` protocol for quality scorer outputs
  - [ ] Add protocol usage examples in docstrings

- [ ] 1.3 **Refactor test_quality.py DataFrame comparisons**
  - [ ] Replace `scored.loc[1, "quality"] > scored.loc[0, "quality"]` with typed accessors
  - [ ] Add explicit `assert isinstance(scored["quality"].dtype, np.dtype)` checks
  - [ ] Use `.iloc[]` with explicit indexing instead of label-based `.loc[]` where appropriate
  - [ ] Add `# type: ignore[union-attr]` with explanation for legitimate heterogeneous comparisons

- [ ] 1.4 **Apply DataFrame type narrowing to test_data_ingestion.py**
  - [ ] Fix lines 167, 359 (int/Timestamp comparison errors)
  - [ ] Add dtype assertions for `created_at`, `updated_at` columns
  - [ ] Document temporal column type expectations

- [ ] 1.5 **Validate DataFrame fixes with mypy**
  - [ ] Run `mypy tests/test_quality.py` and verify error count drops below 50
  - [ ] Run `mypy tests/test_data_ingestion.py` and verify temporal type errors resolved
  - [ ] Run full test suite: `pytest -q tests/test_quality.py tests/test_data_ingestion.py`

## 2. Test Helper Type Annotations (High Priority)

- [ ] 2.1 **Annotate tests/conftest.py fixtures**
  - [ ] Add return type to `pytest_sessionfinish` hook
  - [ ] Annotate `ROOT`, `SRC` path types explicitly
  - [ ] Add type hints to cache/UI fixtures

- [ ] 2.2 **Annotate tests/cli/conftest.py fixtures**
  - [ ] Add `-> CliRunner` return type to `cli_runner` fixture
  - [ ] Add `-> Typer` return type to `cli_app` fixture
  - [ ] Document fixture scopes in docstrings

- [ ] 2.3 **Annotate tests/ui/ fixture files**
  - [ ] Add type hints to `tests/ui/test_run.py` (lines 8, 18-19)
  - [ ] Add type hints to `tests/ui/test_create_app.py` (lines 12, 29, 40, 65)
  - [ ] Add generic type parameters for parametrized fixtures

- [ ] 2.4 **Annotate tests/test_routing.py helper functions**
  - [ ] Add type hints to lines 117, 133, 144, 161 (fixture functions)
  - [ ] Add `ParamSpec` for `_request` override (line 193)
  - [ ] Add explicit `dict[str, ...]` type annotations instead of bare `dict`

- [ ] 2.5 **Annotate tests/test_cli.py helper functions**
  - [ ] Add type hints to lines 20, 52, 95
  - [ ] Add return type annotations for test utilities

- [ ] 2.6 **Validate annotation completeness**
  - [ ] Run `mypy tests/conftest.py --no-error-summary | grep 'no-untyped-def'` (expect 0 matches)
  - [ ] Run `mypy tests/cli/ --no-error-summary | grep 'no-untyped-def'` (expect 0 matches)
  - [ ] Run full test suite to ensure no runtime regressions

## 3. Stub Type Protocol Compliance (Medium Priority)

- [x] 3.1 **Create protocol definitions in tests/io/protocols.py**
  - [x] Define `SessionProtocol` for HTTP client stubs
  - [x] Define `WikidataClientProtocol` with `query` method signature
  - [x] Define `WikipediaClientProtocol` with `get_pageviews` signature
  - [x] Define `RateLimiterProtocol` and `CircuitBreakerProtocol`

- [x] 3.2 **Update StubSession to implement SessionProtocol**
  - [x] Add `request`, `get`, `post` method signatures to match `requests.Session`
  - [x] Implement `response` property for recording/playback
  - [x] Add type hints to `queue_response` method

- [ ] 3.3 **Update WikidataClient stubs in tests/test_data_ingestion.py**
  - [ ] Make `StubClient` (line 335) implement `WikidataClientProtocol`
  - [ ] Make `EmptyClient` (line 469) implement `WikidataClientProtocol`
  - [ ] Make `RecordingClient` implement `WikidataClientProtocol`
  - [ ] Add explicit return types (`dict[str, Any]` vs `dict`)

- [x] 3.4 **Update WikipediaClient stubs in tests/io/enrichment/test_wikipedia.py**
  - [x] Fix `_StubSession` (line 389) to match `Session` protocol
  - [x] Fix `_StubRateLimiter` (line 390) to match `RateLimiter` interface
  - [x] Fix `_StubCircuitBreaker` (line 391) to match `CircuitBreaker` interface
  - [x] Add `CircuitBreaker` to explicit exports in wikipedia module (line 111)

- [ ] 3.5 **Update routing test stubs in tests/test_routing.py**
  - [ ] Make `StubSession` (lines 151, 156, 172, 177, 181) implement `SessionProtocol`
  - [ ] Fix `DummyOTPShortest` (line 267) to implement `OTPClient` protocol
  - [ ] Fix `DummyOTP` (line 316) to implement `OTPClient` protocol
  - [ ] Add explicit return types to `_request` override (line 193)

- [ ] 3.6 **Update EssentialsAccess calculator stub in tests/test_calibration.py**
  - [ ] Make `StubCalculator` (lines 44, 61, 74, 88) implement full `EssentialsAccessCalculator` interface
  - [ ] Add explicit return type annotation (line 19)
  - [ ] Use `Protocol` instead of inheritance if interface is minimal

- [ ] 3.7 **Validate protocol compliance**
  - [ ] Run `mypy tests/io/enrichment/test_wikipedia.py` (expect 0 arg-type errors)
  - [ ] Run `mypy tests/test_routing.py` (expect 0 arg-type errors)
  - [ ] Run `mypy tests/test_calibration.py` (expect 0 arg-type errors)
  - [ ] Run full test suite to ensure stubs still work correctly

## 4. Type Ignore Cleanup (Low Priority)

- [ ] 4.1 **Audit unused type ignores in src/**
  - [ ] Fix `src/Urban_Amenities2/cli/main.py` line 11 (unused ignore)
  - [ ] Review all src modules for unused ignores: `mypy src/ 2>&1 | grep 'unused-ignore'`
  - [ ] Remove or replace with specific error codes

- [ ] 4.2 **Audit unused type ignores in tests/**
  - [ ] Fix `tests/test_cli.py` lines 56, 60
  - [ ] Fix `tests/test_routing.py` lines 88, 95, 183, 225, 249
  - [ ] Fix `tests/io/enrichment/test_wikipedia.py` lines 47, 63, 96, 109, 112, 113, 154, 168, 173
  - [ ] Fix `tests/io/enrichment/test_wikidata.py` lines 76, 86, 111, 112

- [ ] 4.3 **Convert blanket ignores to specific error codes**
  - [ ] Replace `# type: ignore` with `# type: ignore[error-code]`
  - [ ] Add inline comments explaining why ignore is necessary
  - [ ] Link to GitHub issues for technical debt items

- [ ] 4.4 **Document remaining necessary ignores**
  - [ ] Create `docs/TYPE_IGNORES.md` cataloging all remaining ignores
  - [ ] Add justification and removal plan for each
  - [ ] Link to upstream library issues where applicable

- [ ] 4.5 **Validate type ignore cleanup**
  - [ ] Run `mypy src/ tests/ 2>&1 | grep 'unused-ignore'` (expect 0 matches)
  - [ ] Verify total error count decreased by at least 50

## 5. Mypy Configuration Tuning (Low Priority)

- [ ] 5.1 **Enable stricter warnings in pyproject.toml**
  - [ ] Set `warn_unused_ignores = True`
  - [ ] Set `show_error_codes = True`
  - [ ] Set `strict_optional = True`
  - [ ] Set `check_untyped_defs = True`

- [ ] 5.2 **Add per-module overrides for gradual typing**
  - [ ] Add `[[tool.mypy.overrides]]` for `tests/` with `disallow_untyped_defs = false`
  - [ ] Add override for `tests/io/` to allow `Any` in stub implementations
  - [ ] Document migration path to stricter settings

- [ ] 5.3 **Configure error output formatting**
  - [ ] Add `pretty = true` for human-readable output
  - [ ] Add `show_column_numbers = true` for IDE integration
  - [ ] Consider `--html-report` for CI artifacts

- [ ] 5.4 **Integrate mypy into CI pipeline**
  - [ ] Add `mypy src/ --strict` to GitHub Actions workflow
  - [ ] Add `mypy tests/ --check-untyped-defs` as separate CI step
  - [ ] Set failure threshold (e.g., fail if >100 errors)

- [ ] 5.5 **Validate configuration changes**
  - [ ] Run `mypy src/ tests/` with new settings
  - [ ] Verify error count is manageable (<200 total)
  - [ ] Document remaining issues in project README

## 6. Integration & Validation

- [ ] 6.1 **Run full test suite with all changes**
  - [ ] `pytest -q --maxfail=5` (all tests pass)
  - [ ] `pytest --cov=src/Urban_Amenities2 --cov-fail-under=95` (coverage maintained)

- [ ] 6.2 **Run mypy with final configuration**
  - [ ] `mypy src/` (target: 0 errors in production code)
  - [ ] `mypy tests/` (target: <50 errors, down from 890)
  - [ ] Generate error report: `mypy src/ tests/ > mypy_report.txt`

- [ ] 6.3 **Run linters to ensure no style regressions**
  - [ ] `ruff check src tests` (0 errors)
  - [ ] `black --check src tests` (no formatting changes)

- [ ] 6.4 **Update documentation**
  - [ ] Add "Type Safety" section to README
  - [ ] Document mypy configuration in CONTRIBUTING.md
  - [ ] Update pre-commit hooks to include mypy

- [ ] 6.5 **Archive change proposal**
  - [ ] Mark all tasks complete
  - [ ] Run `openspec validate fix-test-type-safety --strict`
  - [ ] Run `openspec archive fix-test-type-safety`
