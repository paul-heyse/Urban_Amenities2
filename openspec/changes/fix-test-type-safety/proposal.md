# Change Proposal: Fix Test Type Safety

## Why

Mypy static type checking currently fails with **890 errors across 86 files**, blocking adoption of strict type safety. The errors cluster into four main categories:

1. **DataFrame type union explosions** (tests/test_quality.py lines 43-101): Pandas DataFrame comparisons with heterogeneous dtypes trigger hundreds of incompatible operator errors
2. **Missing type annotations**: Test fixtures and helper functions lack type hints, causing inference failures
3. **Stub type mismatches**: Test doubles (StubSession, StubClient, etc.) don't satisfy protocol requirements
4. **Stale type ignores**: 20+ `# type: ignore` comments flagged as unused after code refactoring

This blocks:

- CI/CD integration of mypy checks
- IDE type-checking assistance for developers
- Early detection of type-related bugs
- Migration to stricter typing standards

## What Changes

### 1. DataFrame Type Narrowing (High Priority)

- Add explicit type assertions for DataFrame column dtypes in test fixtures
- Replace broad `.loc[]` comparisons with typed accessor patterns
- Introduce `TypedDataFrame` protocols for commonly used test data structures
- Add `# type: ignore[union-attr]` with explanatory comments where unions are legitimate

### 2. Test Helper Type Annotations (High Priority)

- Add complete type signatures to all test fixtures (conftest.py files)
- Annotate pytest fixture return types explicitly
- Add `ParamSpec` and `TypeVar` to generic test utilities
- Document complex generic types with inline comments

### 3. Stub Type Protocol Compliance (Medium Priority)

- Make `StubSession`, `RecordingSession` implement `requests.Session` protocol
- Add `WikidataClient` and `WikipediaClient` protocol definitions
- Update `StubCalculator` to match `EssentialsAccessCalculator` interface
- Use `typing.Protocol` for test doubles instead of inheritance where appropriate

### 4. Type Ignore Cleanup (Low Priority)

- Remove 20+ unused `# type: ignore` comments
- Replace blanket ignores with specific error codes (e.g., `# type: ignore[arg-type]`)
- Document remaining necessary ignores with justification comments
- Add issue references for technical debt ignores

### 5. Mypy Configuration Tuning (Low Priority)

- Enable `warn_unused_ignores = True` permanently
- Add per-module overrides for gradually-typed legacy modules
- Configure `show_error_codes = True` for clearer diagnostics
- Set `strict_optional = True` for better None checking

## Impact

- **Affected specs**: testing
- **Affected code**:
  - `tests/test_quality.py` (DataFrame comparison patterns)
  - `tests/test_routing.py` (stub type mismatches)
  - `tests/test_data_ingestion.py` (union type explosions)
  - `tests/conftest.py` (missing fixture annotations)
  - `tests/cli/conftest.py` (fixture type hints)
  - `tests/io/` (stub protocol implementations)
  - `tests/ui/` (component test annotations)
  - `src/Urban_Amenities2/cli/main.py` (unused ignores)

**Risk**: Changes to test fixtures may require updating dependent tests. Mitigation: Run full test suite after each category of changes.

**Timeline**: Estimate 8-12 hours spread across 3 phases (DataFrame fixes → annotations → stubs).
