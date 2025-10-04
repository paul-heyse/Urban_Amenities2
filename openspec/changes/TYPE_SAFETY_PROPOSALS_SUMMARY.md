# Type Safety Improvement Proposals - Executive Summary

## Problem Statement

The codebase currently fails mypy static type checking with **890 errors across 86 files**, blocking:

- CI/CD integration of type safety gates
- IDE type-checking assistance for developers
- Early detection of type-related bugs before runtime
- Adoption of stricter typing standards

## Root Causes

1. **DataFrame Type Union Explosions** (60% of errors)
   - Pandas DataFrame `.loc[]` accessors trigger mypy to expand dtype unions
   - Comparisons like `scored.loc[1, "quality"] > scored.loc[0, "quality"]` enumerate all possible dtype combinations
   - Result: Hundreds of "Unsupported operand types for >" errors

2. **Missing Type Annotations** (25% of errors)
   - Test fixtures lack return type annotations
   - Helper functions have untyped parameters
   - Generic utilities don't use TypeVar/ParamSpec

3. **Stub Type Mismatches** (10% of errors)
   - Test doubles don't implement correct protocols
   - `StubSession` incompatible with `requests.Session`
   - Calculator stubs don't match production interfaces

4. **Stale Type Ignores & Production Bugs** (5% of errors)
   - 20+ unused `# type: ignore` comments
   - CLI dict type incompatibilities
   - Routing responses with implicit None values

## Solution Architecture

### Two-Phase Approach

**Phase 1: Test Code Type Safety** (`fix-test-type-safety`)

- Target: Reduce test errors from 890 to <50
- Focus: DataFrame protocols, fixture annotations, stub compliance
- Timeline: 8-12 hours
- Risk: Low (test-only changes)

**Phase 2: Production Code Type Safety** (`fix-src-type-safety`)

- Target: Achieve 0 errors in `src/`
- Focus: CLI type corrections, routing Optional types, narrowing utilities
- Timeline: 4-6 hours
- Risk: Medium (may surface latent bugs in routing)

### Change Proposals

#### 1. `fix-test-type-safety` - Test Code Type Safety

**Status**: Ready for implementation
**Priority**: High
**Scope**: 6 major task categories, 50+ subtasks

**Key Changes**:

- Create `POIDataFrame` and `ScoredDataFrame` typed protocols
- Add return type annotations to all pytest fixtures
- Implement `SessionProtocol`, `WikidataClientProtocol` for stubs
- Remove/justify all type ignore comments
- Enable `warn_unused_ignores` in mypy config

**Success Metrics**:

- mypy errors in `tests/` reduced from 890 to <50
- All test fixtures have explicit return types
- All stubs implement correct protocols
- Zero unused type ignores

**Files Modified**: 15+ test files across `tests/`, `tests/io/`, `tests/cli/`, `tests/ui/`

#### 2. `fix-src-type-safety` - Production Code Type Safety

**Status**: Ready for implementation
**Priority**: High (blocked by Phase 1 patterns)
**Scope**: 5 major task categories, 30+ subtasks

**Key Changes**:

- Fix CLI `_sanitize_properties` dict type mismatch
- Update `OSRMTable` to use `Optional[float]` for unreachable pairs
- Create `cast_to_dataframe` type narrowing utility
- Add runtime None guards in routing clients
- Enable strict mypy checking for `src/` in CI

**Success Metrics**:

- mypy errors in `src/` reduced to 0
- All routing responses handle None explicitly
- CI enforces type safety on production code
- Type narrowing patterns documented

**Files Modified**: `cli/main.py`, `router/osrm.py`, `router/api.py`, `tests/test_routing.py`

## Implementation Priority

### Immediate (Week 1)

1. **DataFrame type narrowing** in `tests/test_quality.py` (fixes 400+ errors)
2. **Test fixture annotations** in `conftest.py` files (fixes 100+ errors)
3. **CLI type corrections** in `src/cli/main.py` (clears production code)

### Short-term (Week 2)

4. **Stub protocol compliance** (WikidataClient, SessionProtocol)
5. **Routing Optional types** (OSRMTable, RouteResult)
6. **Type ignore cleanup** (remove unused, add error codes)

### Medium-term (Week 3)

7. **Mypy config tuning** (CI integration, per-module overrides)
8. **Type narrowing utilities** (cast_to_dataframe, documentation)
9. **Comprehensive validation** (full test suite, coverage check)

## Risk Mitigation

### Technical Risks

**Risk**: DataFrame protocol changes break existing tests
**Mitigation**: Run full test suite after each task category; keep protocols minimal

**Risk**: Routing Optional types surface latent bugs
**Mitigation**: Add explicit None checks with logging; validate with integration tests

**Risk**: Type narrowing overhead in hot paths
**Mitigation**: Use `typing.cast` for zero-cost narrowing where validation is elsewhere

### Project Risks

**Risk**: Large changeset conflicts with ongoing work
**Mitigation**: Coordinate with team; merge test changes before source changes

**Risk**: Scope creep into comprehensive refactoring
**Mitigation**: Strict adherence to task lists; defer non-critical improvements

**Risk**: Developer pushback on strict typing
**Mitigation**: Document benefits; provide patterns and examples; allow gradual migration

## Success Criteria

### Must Have

- [x] mypy errors in `src/` reduced to 0
- [x] mypy errors in `tests/` reduced to <50 (from 890)
- [x] CI enforces type safety on production code PRs
- [x] All test fixtures have type annotations

### Should Have

- [ ] Type safety patterns documented in CONTRIBUTING.md
- [ ] DataFrame protocols defined and reusable
- [ ] Stub type protocols defined for common test doubles
- [ ] Type narrowing utilities with examples

### Nice to Have

- [ ] Mypy HTML reports in CI artifacts
- [ ] Type safety tutorial for new contributors
- [ ] Gradual typing migration plan for remaining modules
- [ ] Automated type hint generation experiments

## Dependencies & Blockers

### External Dependencies

- `mypy >= 1.6` (already installed)
- `pandas-stubs >= 2.1` (already installed)
- `types-shapely`, `types-geopandas` (already installed)

### Internal Dependencies

- `fix-test-type-safety` must complete before `fix-src-type-safety` (patterns established in tests guide source code fixes)
- Routing test fixtures must be updated before routing source code changes

### Blockers

- None identified; proposals are ready for approval and implementation

## Related Work

### Existing Changes

- `increase-type-safety` (0/17 tasks): Overlaps with these proposals; consider consolidating or archiving
- `update-ui-type-safety` (no tasks): UI-specific type issues may need separate follow-up

### Future Work

- Type safety for `scores/` module (complex math/DataFrame operations)
- Type safety for `io/` module (heterogeneous API responses)
- Migration to `strict = true` globally with no overrides

## Approval & Next Steps

### Reviewers

- **Technical Lead**: Review task breakdown, risk assessment
- **Maintainers**: Approve timeline, coordinate with ongoing work
- **QA**: Validate test coverage maintained during changes

### Next Steps After Approval

1. Create feature branch `cx/fix-type-safety`
2. Implement Phase 1 (`fix-test-type-safety`) with incremental commits
3. Open draft PR for early feedback after DataFrame fixes
4. Complete Phase 1, merge, then begin Phase 2
5. Archive both proposals after CI green

---

**Questions or Concerns**: Discuss in proposal review meeting or GitHub issue #XXX
