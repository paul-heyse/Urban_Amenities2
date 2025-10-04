# Type Safety Fixes - Quick Start Guide

## For Implementers

### Before Starting

```bash
# Understand current error landscape
mypy src/ tests/ 2>&1 | tee mypy_baseline.txt
mypy src/ tests/ 2>&1 | grep -c "error:"  # Expect: ~890

# Ensure clean test baseline
pytest -q
ruff check src tests
```

### Phase 1: Test Type Safety (fix-test-type-safety)

#### Quick Win: DataFrame Type Narrowing (2-3 hours)

**Fixes ~400 errors in tests/test_quality.py**

```python
# BEFORE (triggers union explosion)
assert scored.loc[1, "quality"] > scored.loc[0, "quality"]

# AFTER (explicit dtype assertion)
quality_col = scored["quality"].astype(float)
assert quality_col.iloc[1] > quality_col.iloc[0]

# OR with typed accessor
assert float(scored.loc[1, "quality"]) > float(scored.loc[0, "quality"])
```

**Task**: Open `tests/test_quality.py` and apply pattern to lines 43, 44, 101.

#### Quick Win: Fixture Type Annotations (1-2 hours)

**Fixes ~100 errors across conftest.py files**

```python
# BEFORE
@pytest.fixture
def cli_runner():
    return CliRunner()

# AFTER
@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()
```

**Task**: Annotate all fixtures in `tests/conftest.py`, `tests/cli/conftest.py`, `tests/io/conftest.py`.

#### Quick Win: Remove Unused Ignores (30 min)

**Fixes ~20 errors**

```bash
# Find unused ignores
mypy src/ tests/ 2>&1 | grep "unused-ignore"

# Remove each one and verify mypy still passes that line
# Then rerun tests to ensure no runtime issues
```

### Phase 2: Source Type Safety (fix-src-type-safety)

#### Quick Win: CLI Type Corrections (1 hour)

**Achieves 0 errors in cli/main.py**

```python
# Fix 1: Remove unused ignore (line 11)
# Just delete the comment after verifying mypy is happy

# Fix 2: Dict type mismatch (line 442)
properties_dict: Mapping[str, object] = {
    str(k): v for k, v in properties.items()
}
result = _sanitize_properties(properties_dict)

# Fix 3: DataFrame/Series union (line 507)
result = some_operation()
if isinstance(result, pd.Series):
    result = result.to_frame()
assert isinstance(result, pd.DataFrame)
frame: pd.DataFrame = result
```

#### Quick Win: Routing Optional Types (2 hours)

**Fixes all routing type errors**

```python
# Update OSRMTable dataclass (src/Urban_Amenities2/router/osrm.py)
@dataclass
class OSRMTable:
    durations: list[list[float | None]]  # Changed from list[list[float]]
    distances: list[list[float | None]] | None  # Already Optional at top level

    def get_duration(self, i: int, j: int) -> float | None:
        """Get duration with None check."""
        return self.durations[i][j]

# Update test fixtures (tests/test_routing.py)
mock_table = OSRMTable(
    durations=[[0.0, 120.0], [130.0, 0.0]],  # Can now include None
    distances=[[0.0, 1200.0], [1300.0, 0.0]],
)
```

### Validation Checkpoints

After **each** quick win:

```bash
# 1. Verify mypy error count decreased
mypy src/ tests/ 2>&1 | grep -c "error:"

# 2. Verify tests still pass
pytest -q --maxfail=5

# 3. Verify no lint regressions
ruff check src tests

# 4. Commit incrementally
git add -p  # Stage only related changes
git commit -m "fix(types): <description>"
```

### Common Patterns Reference

#### Pattern 1: DataFrame Column Type Assertion

```python
# When you know column dtype but mypy doesn't
df["numeric_col"] = pd.to_numeric(df["numeric_col"], errors="coerce")
values: pd.Series = df["numeric_col"].astype(float)
```

#### Pattern 2: Protocol for Test Stubs

```python
# Define protocol (tests/io/protocols.py)
from typing import Protocol

class WikidataClientProtocol(Protocol):
    def query(self, sparql: str) -> dict[str, Any]: ...

# Implement in stub (tests/test_data_ingestion.py)
class StubClient:
    def query(self, sparql: str) -> dict[str, Any]:
        return {"results": []}
```

#### Pattern 3: Type Narrowing with Runtime Check

```python
from typing import cast

result: pd.DataFrame | pd.Series[Any] = some_operation()

# Option A: Runtime validation
if isinstance(result, pd.Series):
    raise TypeError("Expected DataFrame, got Series")
frame: pd.DataFrame = result

# Option B: Zero-cost cast (use when validation is elsewhere)
frame: pd.DataFrame = cast(pd.DataFrame, result)
```

#### Pattern 4: Explicit Optional Handling

```python
# BEFORE
duration = response["duration"]  # Might be None!

# AFTER
duration: float | None = response.get("duration")
if duration is not None:
    total_time += duration
```

### Troubleshooting

#### "Unsupported operand types for >"

**Cause**: Pandas dtype union explosion
**Fix**: Cast to explicit dtype or use `.astype(float)`

#### "Function is missing a return type annotation"

**Cause**: Pytest fixture or helper lacks `-> Type`
**Fix**: Add explicit return type annotation

#### "Argument has incompatible type"

**Cause**: Stub doesn't match protocol
**Fix**: Implement full interface or use `Protocol` instead of inheritance

#### "Unused type ignore comment"

**Cause**: Error was fixed but ignore remains
**Fix**: Delete the `# type: ignore` comment

### Progress Tracking

Create a simple tracking file:

```bash
# Track error count over time
echo "$(date +%Y-%m-%d) $(mypy src/ tests/ 2>&1 | grep -c 'error:')" >> mypy_progress.txt

# Visualize progress
cat mypy_progress.txt
# 2025-10-04 890
# 2025-10-04 450  (after DataFrame fixes)
# 2025-10-04 350  (after fixture annotations)
# ...
```

### Getting Help

- **Mypy errors confusing?** Check: <https://mypy.readthedocs.io/en/stable/error_codes.html>
- **Pattern not working?** Review `TYPE_SAFETY_PROPOSALS_SUMMARY.md` for alternatives
- **Tests breaking?** Revert last change and try incremental approach
- **Blocked?** Mark task as in-progress in `tasks.md` and move to next task

### Final Validation

Before marking proposals complete:

```bash
# Production code: 0 errors required
mypy src/ --strict
echo "Exit code should be 0: $?"

# Test code: <50 errors acceptable
mypy tests/ 2>&1 | grep -c "error:"
# Should be <50 (down from 890)

# All tests pass
pytest -q

# Coverage maintained
pytest --cov=src/Urban_Amenities2 --cov-fail-under=95

# Linters happy
ruff check src tests
black --check src tests
```

## For Reviewers

### Key Review Points

1. **No Runtime Regressions**: All tests pass, coverage maintained
2. **Type Safety Improved**: Mypy error count decreased measurably
3. **Patterns Consistent**: Uses established patterns from proposals
4. **Documentation Updated**: Comments explain non-obvious type narrowing
5. **Incremental Commits**: Changes grouped logically for easy review

### Review Commands

```bash
# Check type safety improvement
git diff main --stat | grep -E "(src|tests)"
mypy src/ tests/  # Compare to baseline

# Verify test coverage
pytest --cov=src/Urban_Amenities2 --cov-report=html
open htmlcov/index.html

# Check for unintended changes
git diff main src/ | grep -E "^[-+]" | head -50
```

### Approval Criteria

- [ ] Mypy errors in `src/` reduced to 0 (for fix-src-type-safety)
- [ ] Mypy errors in `tests/` reduced by >80% (for fix-test-type-safety)
- [ ] All tests pass with no new flakes
- [ ] Coverage remains ≥95%
- [ ] No ruff/black violations introduced
- [ ] Type narrowing patterns documented
