# Implementation Tasks: Fix Source Code Type Safety

## 1. CLI Type Corrections (High Priority)

- [x] 1.1 **Remove unused type ignore in cli/main.py**
  - [x] Review line 11 to understand original ignore purpose
  - [x] Verify mypy no longer reports error without ignore
  - [x] Remove `# type: ignore` comment
  - [x] Run `mypy src/Urban_Amenities2/cli/main.py` to confirm

- [x] 1.2 **Fix _sanitize_properties type mismatch (line 442)**
  - [x] Review `_sanitize_properties` function signature
  - [x] Identify why `dict[Hashable, Any]` incompatible with `Mapping[str, object]`
  - [x] Option A: Cast Hashable keys to str with validation
  - [x] Option B: Update function to accept `Mapping[Hashable, object]`
  - [x] Add test case for non-string keys if accepted

- [x] 1.3 **Fix DataFrame/Series union assignment (line 507)**
  - [x] Review code context: what operation returns `DataFrame | Series[Any]`?
  - [x] Add explicit type narrowing: `if isinstance(result, pd.DataFrame): ...`
  - [x] Document when Series is expected vs DataFrame
  - [x] Add runtime assertion if DataFrame is guaranteed

- [ ] 1.4 **Validate CLI type corrections**
  - [ ] Run `mypy src/Urban_Amenities2/cli/main.py` (expect 0 errors)
  - [ ] Run CLI integration tests: `pytest tests/cli/ -v`
  - [ ] Manually test `ingest` and `score` commands

## 2. Routing Response Type Safety (High Priority)

- [ ] 2.1 **Analyze OSRMTable None value semantics**
  - [ ] Review OSRM API docs for when `null` durations/distances occur
  - [ ] Check if `None` represents unreachable pairs or missing data
  - [ ] Document expected None behavior in docstrings

- [x] 2.2 **Update OSRMTable dataclass type hints**
  - [x] Change `durations: list[list[float]]` to `list[list[float | None]]`
  - [x] Change `distances: list[list[float]]` to `list[list[float | None]]` (already Optional at top level)
  - [x] Update `__post_init__` validation to handle None values
  - [x] Add docstring examples with None values

- [x] 2.3 **Update test fixtures in test_routing.py**
  - [ ] Fix line 40: change `list[list[float]]` to `list[list[float | None]]`
  - [ ] Fix line 228: update durations fixture to match new type
  - [x] Add test case with None values in matrix (unreachable pair)
  - [x] Verify matrix indexing handles None correctly

- [x] 2.4 **Add runtime None handling in routing clients**
  - [x] Review `OSRMClient.table()` response parsing
  - [x] Add explicit None checks before using duration/distance values
  - [x] Document how `RoutingAPI.matrix()` handles None (drop rows? fill with inf?)
  - [ ] Add integration test with unreachable OD pairs

- [ ] 2.5 **Fix test_routing.py type errors (lines 52-68)**
  - [ ] Line 52: Add None check before `< 300` comparison
  - [ ] Lines 54-55: Add type assertions for indexable access
  - [ ] Line 67-68: Update to handle Optional distances
  - [ ] Lines 127, 130, 271, 323-335: Add type guards for metadata access

- [ ] 2.6 **Validate routing type corrections**
  - [ ] Run `mypy src/Urban_Amenities2/router/` (expect 0 errors)
  - [ ] Run `mypy tests/test_routing.py` (expect <10 errors)
  - [ ] Run routing tests: `pytest tests/test_routing.py -v`

## 3. Type Narrowing Patterns (Medium Priority)

- [x] 3.1 **Create type narrowing utilities in src/Urban_Amenities2/utils/types.py**
  - [ ] Implement `cast_to_dataframe(obj: DataFrame | Series[Any]) -> DataFrame`
  - [ ] Add runtime validation raising TypeError if Series
  - [ ] Implement `ensure_dataframe(obj: DataFrame | Series[Any]) -> DataFrame` (coerce Series)
  - [ ] Add docstrings with usage examples

- [x] 3.2 **Apply type narrowing in cli/main.py**
  - [ ] Replace bare assignment at line 507 with `cast_to_dataframe(result)`
  - [ ] Add try/except to provide helpful error message
  - [ ] Document when narrowing is safe vs needs runtime check

- [x] 3.3 **Document type narrowing patterns**
  - [ ] Add "Type Safety Patterns" section to CONTRIBUTING.md
  - [ ] Explain `isinstance` check + narrowing pattern
  - [ ] Explain `typing.cast` vs runtime validation
  - [ ] Provide decision tree: when to use each approach

- [x] 3.4 **Validate type narrowing utilities**
  - [ ] Add unit tests for `cast_to_dataframe` success and failure cases
  - [ ] Run `mypy src/Urban_Amenities2/utils/types.py` (0 errors)
  - [ ] Verify CLI no longer has DataFrame/Series type errors

## 4. Optional Type Handling (Medium Priority)

- [ ] 4.1 **Audit routing module for implicit None**
  - [ ] Search for `.get()` calls on dicts without default values
  - [ ] Search for list indexing without bounds checks
  - [ ] Identify all locations that could raise KeyError/IndexError

- [ ] 4.2 **Add explicit Optional annotations**
  - [ ] Update `OSRMRoute.duration` if can be None
  - [ ] Update `OSRMRoute.distance` if can be None
  - [ ] Update `RouteResult.metadata` dict values to explicit types
  - [ ] Document when None is expected vs error condition

- [ ] 4.3 **Add runtime None guards**
  - [ ] Wrap Optional value access with `if value is not None:`
  - [ ] Use `.get(key, default)` instead of `[key]` for optional dict values
  - [ ] Add explicit error messages for unexpected None
  - [ ] Log warnings for None values in production data

- [ ] 4.4 **Add tests for None value handling**
  - [ ] Test routing with unreachable destination (expect None or error)
  - [ ] Test empty routing response (no itineraries found)
  - [ ] Test partial failures (some OD pairs succeed, some None)
  - [ ] Verify graceful degradation vs hard failure

- [ ] 4.5 **Validate Optional type handling**
  - [ ] Run `mypy src/Urban_Amenities2/router/` with `strict_optional=True`
  - [ ] Run full routing test suite with coverage
  - [ ] Review coverage report for uncovered None branches

## 5. Integration & Validation

- [ ] 5.1 **Run mypy on all source code**
  - [ ] `mypy src/Urban_Amenities2/cli/` (expect 0 errors)
  - [ ] `mypy src/Urban_Amenities2/router/` (expect 0 errors)
  - [ ] `mypy src/Urban_Amenities2/` (expect 0 errors in all modules)

- [ ] 5.2 **Run full test suite**
  - [ ] `pytest -q` (all tests pass)
  - [ ] `pytest --cov=src/Urban_Amenities2 --cov-fail-under=95` (coverage maintained)
  - [ ] Review coverage for new None-handling branches

- [ ] 5.3 **Run linters**
  - [ ] `ruff check src/` (0 errors)
  - [ ] `black --check src/` (no formatting issues)

- [ ] 5.4 **Update documentation**
  - [ ] Add "Type Safety Standards" to CONTRIBUTING.md
  - [ ] Document Optional type conventions
  - [ ] Add examples to module docstrings

- [ ] 5.5 **Archive change proposal**
  - [ ] Mark all tasks complete
  - [ ] Run `openspec validate fix-src-type-safety --strict`
  - [ ] Run `openspec archive fix-src-type-safety`
