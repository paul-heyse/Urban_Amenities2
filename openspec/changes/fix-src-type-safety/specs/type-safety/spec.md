# Type Safety Capability Specification Delta

## ADDED Requirements

### Requirement: Production Code Mypy Compliance

All production code in `src/` SHALL pass mypy static type checking with zero errors when `strict = true`.

#### Scenario: CLI module type correctness

- **WHEN** mypy analyzes `src/Urban_Amenities2/cli/main.py`
- **THEN** all function calls SHALL have compatible argument types
- **AND** all variable assignments SHALL have compatible types
- **AND** no unused `# type: ignore` comments SHALL remain

#### Scenario: Routing module type correctness

- **WHEN** mypy analyzes `src/Urban_Amenities2/router/` modules
- **THEN** all Optional types SHALL be explicitly annotated
- **AND** all None value dereferences SHALL have runtime guards
- **AND** all dataclass fields SHALL have precise types (including `Optional[T]` where applicable)

#### Scenario: Type ignore elimination

- **WHEN** a `# type: ignore` comment exists in production code
- **THEN** the underlying type error SHALL be fixed rather than suppressed
- **OR** if legitimately unfixable, the ignore SHALL have a specific error code and justification comment

### Requirement: Routing Response Optional Type Safety

Routing client responses SHALL explicitly model optional values (e.g., unreachable destinations) using `Optional[T]` annotations.

#### Scenario: OSRM table matrix with unreachable pairs

- **WHEN** OSRM `/table` API returns `null` for an unreachable origin-destination pair
- **THEN** `OSRMTable.durations` SHALL be typed as `list[list[float | None]]`
- **AND** `OSRMTable.distances` SHALL be typed as `list[list[float | None]] | None`
- **AND** code accessing matrix values SHALL check for None before arithmetic operations

#### Scenario: OTP route with no valid itineraries

- **WHEN** OpenTripPlanner returns an empty itineraries list
- **THEN** `RouteResult.metadata` SHALL indicate failure reason
- **AND** calling code SHALL handle missing route gracefully (not crash)

#### Scenario: Runtime validation of routing responses

- **WHEN** a routing client parses an API response
- **THEN** unexpected None values SHALL be logged as warnings
- **AND** critical None values (e.g., missing duration) SHALL raise `ValueError` with context
- **AND** tests SHALL cover both success and None-handling paths

### Requirement: Type Narrowing Utilities

The codebase SHALL provide utilities for safely narrowing union types with runtime validation.

#### Scenario: DataFrame vs Series narrowing

- **WHEN** a pandas operation returns `DataFrame | Series[Any]` but caller expects DataFrame
- **THEN** a `cast_to_dataframe(obj)` utility SHALL perform runtime `isinstance` check
- **AND** the utility SHALL raise `TypeError` with helpful message if Series received
- **AND** mypy SHALL accept the narrowed type after the utility call

#### Scenario: Optional value unwrapping

- **WHEN** a value is `Optional[T]` but caller expects `T` after validation
- **THEN** code SHALL use `if value is not None:` to narrow type
- **OR** use `assert value is not None` with explanatory comment
- **AND** mypy SHALL understand the type narrowing in the narrowed scope

#### Scenario: Dict key type narrowing

- **WHEN** a dict has `Hashable` keys but function expects `str` keys
- **THEN** code SHALL validate all keys are strings with `all(isinstance(k, str) for k in d.keys())`
- **OR** cast individual keys with runtime validation
- **AND** mypy SHALL accept the narrowed `dict[str, V]` type

### Requirement: Type Annotation Completeness

All public functions in production code SHALL have complete type annotations including parameters, return types, and exceptions.

#### Scenario: Function parameter types

- **WHEN** a function accepts arguments
- **THEN** each parameter SHALL have an explicit type annotation
- **AND** complex types (e.g., DataFrame) SHALL use protocol types or TypeVar where appropriate
- **AND** default values SHALL match the declared type

#### Scenario: Function return types

- **WHEN** a function returns a value
- **THEN** the return type SHALL be explicitly annotated
- **AND** `None` returns SHALL use `-> None` not omitted annotation
- **AND** union returns SHALL use `Union[T, U]` or `T | U` syntax

#### Scenario: Generic function types

- **WHEN** a function operates on multiple types uniformly
- **THEN** the function SHALL use `TypeVar` with appropriate constraints
- **AND** the TypeVar SHALL be defined at module level with descriptive name
- **AND** type constraints SHALL be documented in docstring

## MODIFIED Requirements

### Requirement: Routing Response Dataclasses (Modified)

Routing response dataclasses SHALL use precise types that reflect actual API behavior including optional fields.

*(Previous requirement used non-optional `float` types; now requires `Optional[float]` where APIs return null)*

#### Scenario: OSRMTable with optional values

- **WHEN** creating an `OSRMTable` instance from API response
- **THEN** `durations` field SHALL accept `list[list[float | None]]`
- **AND** `distances` field SHALL accept `Optional[list[list[float | None]]]`
- **AND** `__post_init__` validation SHALL allow None values in matrices

#### Scenario: RouteResult metadata optional fields

- **WHEN** creating a `RouteResult` from OSRM or OTP response
- **THEN** metadata dict values SHALL be typed as `str | float | int | None`
- **AND** accessing optional metadata SHALL use `.get(key, default)`
- **AND** critical metadata (e.g., duration) SHALL be validated as present

## ADDED Requirements (continued)

### Requirement: Mypy Configuration Enforcement

The project SHALL maintain mypy configuration that enables strict checking for production code while allowing gradual migration.

#### Scenario: Strict mode for src/

- **WHEN** mypy runs on `src/Urban_Amenities2/` modules
- **THEN** `strict = true` SHALL be enabled
- **AND** `warn_unused_ignores = True` SHALL catch stale ignores
- **AND** `show_error_codes = True` SHALL provide actionable error messages

#### Scenario: CI mypy gate for production code

- **WHEN** a pull request modifies files in `src/`
- **THEN** CI SHALL run `mypy src/ --strict` and fail on any errors
- **AND** the error report SHALL be attached to PR as comment
- **AND** developers SHALL fix errors before merge approval

#### Scenario: Error code documentation

- **WHEN** mypy reports an error with code (e.g., `[arg-type]`)
- **THEN** CONTRIBUTING.md SHALL document common error codes and fixes
- **AND** examples SHALL show before/after code for typical errors
- **AND** links to mypy docs SHALL be provided for detailed explanations
