# Change Proposal: Fix Source Code Type Safety

## Why

Production code (`src/`) has type safety issues preventing full mypy compliance, including:

1. **Unused type ignores**: `src/Urban_Amenities2/cli/main.py` line 11 flagged as unused
2. **Dict type incompatibilities**: `cli/main.py` line 442 passes `dict[Hashable, Any]` where `Mapping[str, object]` expected
3. **DataFrame/Series ambiguity**: `cli/main.py` line 507 assigns `DataFrame | Series[Any]` to `DataFrame` variable
4. **Routing stub types**: `tests/test_routing.py` lines 40+ have OSRMTable type mismatches with `None` values

These errors:

- Block CI integration of strict mypy checks on production code
- Hide potential runtime bugs (e.g., unexpected None values in routing responses)
- Create inconsistent type safety standards across modules

## What Changes

### 1. CLI Type Corrections (High Priority)

- Fix unused type ignore at `cli/main.py` line 11
- Fix `_sanitize_properties` call at line 442 to accept correct dict type
- Add explicit type narrowing at line 507 for DataFrame/Series union
- Document edge cases where unions are legitimate

### 2. Routing Response Type Safety (High Priority)

- Update `OSRMTable` dataclass to correctly model `Optional[float]` in duration/distance matrices
- Fix test fixtures in `tests/test_routing.py` to use `Optional[float]` consistently
- Add runtime validation for None values in routing responses
- Update `RouteResult` type hints to reflect actual OSRM/OTP behavior

### 3. Type Narrowing Patterns (Medium Priority)

- Add helper functions for safe DataFrame/Series narrowing
- Create `cast_to_dataframe` utility with runtime validation
- Document when to use `isinstance` checks vs `cast` for type narrowing
- Add examples to style guide

### 4. Optional Type Handling (Medium Priority)

- Review all routing client responses for `None` value handling
- Add explicit `Optional[]` annotations where values can be missing
- Use `strictNullChecks`-equivalent patterns in comparisons
- Add runtime guards for None dereferences

## Impact

- **Affected specs**: routing-engines, type-safety
- **Affected code**:
  - `src/Urban_Amenities2/cli/main.py` (type corrections)
  - `src/Urban_Amenities2/router/osrm.py` (Optional type annotations)
  - `tests/test_routing.py` (fixture type corrections)

**Risk**: Changes to routing response types may surface latent bugs in distance/duration handling. Mitigation: Add explicit None checks and validate with existing integration tests.

**Benefit**: Achieving 0 mypy errors in `src/` enables CI enforcement and catches bugs earlier.

**Timeline**: Estimate 4-6 hours for implementation and validation.
