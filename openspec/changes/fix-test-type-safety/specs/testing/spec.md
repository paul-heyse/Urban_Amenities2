# Testing Capability Specification Delta

## ADDED Requirements

### Requirement: Static Type Checking in Tests

Test code SHALL be compatible with mypy static type analysis to enable early bug detection and IDE type assistance.

#### Scenario: DataFrame type assertions in quality tests

- **WHEN** a test fixture creates a DataFrame with specific column dtypes (e.g., `quality: float64`, `poi_id: object`)
- **THEN** mypy SHALL infer column types correctly from explicit dtype annotations or type assertions
- **AND** comparisons between DataFrame values SHALL not trigger union type explosion errors

#### Scenario: Test fixture type annotations

- **WHEN** a pytest fixture returns a value used across multiple tests
- **THEN** the fixture function SHALL have an explicit return type annotation
- **AND** mypy SHALL propagate the type to dependent test functions

#### Scenario: Protocol compliance for test doubles

- **WHEN** a test stub replaces a production dependency (e.g., `WikidataClient`, `requests.Session`)
- **THEN** the stub SHALL implement the same protocol or interface as the real dependency
- **AND** mypy SHALL accept the stub as a valid substitution in function calls

#### Scenario: Type ignore justification

- **WHEN** a `# type: ignore` comment is necessary due to library limitations or legitimate type unsafety
- **THEN** the ignore SHALL specify the exact error code (e.g., `# type: ignore[arg-type]`)
- **AND** an inline comment SHALL explain why the ignore is required
- **AND** the ignore SHALL be removed if mypy no longer reports an error

#### Scenario: Gradual typing in test modules

- **WHEN** a test module is being migrated to full type safety incrementally
- **THEN** mypy configuration SHALL allow per-module `disallow_untyped_defs = false` overrides
- **AND** a documented migration plan SHALL track progress toward strict typing

### Requirement: Type Safety Error Budget

The test suite SHALL maintain a bounded count of mypy type errors to prevent type safety degradation.

#### Scenario: Error count baseline

- **WHEN** mypy runs on the full codebase after type safety improvements
- **THEN** production code (`src/`) SHALL have 0 mypy errors
- **AND** test code (`tests/`) SHALL have fewer than 50 mypy errors (down from 890)

#### Scenario: CI mypy gate

- **WHEN** a pull request modifies Python source code
- **THEN** CI SHALL run `mypy src/ tests/` and report error counts
- **AND** CI SHALL fail if production code introduces new mypy errors
- **AND** CI SHALL warn (but not fail) if test errors increase by >10

#### Scenario: Type ignore cleanup tracking

- **WHEN** unused `# type: ignore` comments are detected by mypy
- **THEN** the developer SHALL remove the ignore or replace it with a specific error code
- **AND** CI SHALL enforce `warn_unused_ignores = True` to catch stale ignores

### Requirement: Typed DataFrame Protocols

Test fixtures creating pandas DataFrames SHALL use typed protocols to document expected column schemas.

#### Scenario: POI DataFrame protocol

- **WHEN** a test creates a DataFrame representing points of interest
- **THEN** a `POIDataFrame` protocol SHALL define column names and dtypes
- **AND** test fixtures SHALL be annotated with the protocol type
- **AND** mypy SHALL verify column access matches the protocol

#### Scenario: Scored DataFrame protocol

- **WHEN** a quality scorer returns a DataFrame with computed metrics
- **THEN** a `ScoredDataFrame` protocol SHALL define output columns (e.g., `quality: float64`)
- **AND** comparison operations SHALL use protocol-typed accessors
- **AND** mypy SHALL validate comparison operands have compatible types

#### Scenario: Protocol documentation

- **WHEN** a new DataFrame protocol is defined
- **THEN** a docstring SHALL list all required columns and their dtypes
- **AND** usage examples SHALL demonstrate typed accessor patterns
- **AND** the protocol SHALL be exported from `tests/fixtures/types.py`

## MODIFIED Requirements

### Requirement: Test Helper Functions (Modified)

Test helper functions and fixtures SHALL have complete type annotations including parameters, return types, and generic type parameters.

*(Previous requirement allowed untyped helpers; now requires full annotation)*

#### Scenario: Pytest fixture return types

- **WHEN** a pytest fixture provides a dependency to tests
- **THEN** the fixture function SHALL have an explicit return type annotation
- **AND** the annotation SHALL use concrete types (e.g., `CliRunner`) not `Any`

#### Scenario: Generic test utilities

- **WHEN** a test utility function works with multiple types (e.g., DataFrame validators)
- **THEN** the function SHALL use `TypeVar` or `ParamSpec` for generic parameters
- **AND** type constraints SHALL be documented in docstrings

#### Scenario: Parametrized fixture types

- **WHEN** a pytest fixture is parametrized with multiple values
- **THEN** the return type SHALL be a union if values have different types
- **OR** values SHALL be cast to a common protocol/interface type

## ADDED Requirements (continued)

### Requirement: Stub Type Protocol Implementation

Test doubles (stubs, mocks, fakes) SHALL implement the same interface as the production dependencies they replace.

#### Scenario: HTTP client stub protocol

- **WHEN** a `StubSession` replaces `requests.Session` in tests
- **THEN** `StubSession` SHALL implement a `SessionProtocol` defining `get`, `post`, `request` methods
- **AND** method signatures SHALL match `requests.Session` argument names and types
- **AND** mypy SHALL accept `StubSession` wherever `Session` is expected

#### Scenario: Wikidata client stub

- **WHEN** a test uses `StubClient` to replace `WikidataClient`
- **THEN** `StubClient` SHALL implement `WikidataClientProtocol` with `query(sparql: str) -> dict[str, Any]`
- **AND** the stub SHALL be accepted as a valid `WikidataClient` argument

#### Scenario: Calculator stub interface

- **WHEN** `StubCalculator` replaces `EssentialsAccessCalculator` in calibration tests
- **THEN** `StubCalculator` SHALL implement the full calculator protocol including `compute()` signature
- **AND** mypy SHALL verify the stub satisfies type requirements

### Requirement: Mypy Configuration Standards

The project SHALL maintain mypy configuration that balances strict type checking with gradual migration pragmatism.

#### Scenario: Production code strictness

- **WHEN** mypy analyzes `src/` modules
- **THEN** configuration SHALL enable `strict = true` for maximum safety
- **AND** `disallow_untyped_defs = false` SHALL allow gradual function annotation

#### Scenario: Test code leniency

- **WHEN** mypy analyzes `tests/` modules
- **THEN** configuration SHALL use per-module overrides to allow `Any` in stub implementations
- **AND** `check_untyped_defs = True` SHALL still validate annotated test functions

#### Scenario: Diagnostic clarity

- **WHEN** mypy reports type errors
- **THEN** configuration SHALL enable `show_error_codes = True` for specific error references
- **AND** configuration SHALL enable `pretty = true` for readable output
- **AND** configuration SHALL enable `show_column_numbers = true` for IDE integration

#### Scenario: Library stub handling

- **WHEN** a third-party library lacks type stubs (e.g., `geopandas`, `google.transit`)
- **THEN** mypy configuration SHALL use `[[tool.mypy.overrides]]` to ignore missing imports
- **AND** a TODO comment SHALL track when upstream stubs become available
