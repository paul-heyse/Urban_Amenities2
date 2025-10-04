# Change Proposal: Add Math Module Test Coverage

## Why

The `Urban_Amenities2.math` module currently has 81.69% test coverage, below the 90% target threshold. Mathematical kernels are the foundation of AUCS scoring, and untested code paths can lead to:

- Incorrect accessibility scores propagating silently through the system
- Violations of mathematical invariants (monotonicity, homogeneity, bounds)
- Edge case failures with extreme input values (overflow, underflow, division by zero)

The most critical gaps:

- `math/ces.py`: 78.95% coverage (missing overflow handling, rho edge cases)
- `math/diversity.py`: 79.78% coverage (missing satiation parameter validation)
- `math/satiation.py`: 34.48% coverage (core satiation logic largely untested)

Mathematical functions must be exhaustively tested with property-based tests to ensure behavioral correctness across the input space.

## What Changes

### High-Priority Coverage Additions

**CES Aggregation (`math/ces.py`):**

- Test edge cases for elasticity parameter ρ:
  - ρ → 0 (Cobb-Douglas limit)
  - ρ → 1 (linear aggregation)
  - ρ < 0 (complementary goods)
  - ρ > 10 (near-perfect substitutes)
- Test overflow handling with large input values
- Test underflow handling with very small inputs
- Test monotonicity property: increasing any input increases output
- Test homogeneity property: scaling all inputs by k scales output by k^(1/ρ)
- Test bounds: output never exceeds max input when ρ > 0

**Satiation Function (`math/satiation.py`):**

- Test core satiation curve: `w(n) = (1 - exp(-λn)) / n`
- Test λ parameter sensitivity (small λ → weak satiation, large λ → strong satiation)
- Test behavior at n=0 (undefined input handling)
- Test behavior at n=1 (trivial case: w(1) = 1 - exp(-λ))
- Test large n behavior (w(n) → 0 as n → ∞)
- Test vectorized operations on arrays of amenity counts
- Property test: w(n) is monotonically decreasing in n

**Diversity Bonus (`math/diversity.py`):**

- Test category diversity calculation for uniform and skewed distributions
- Test entropy-based diversity metric
- Test Simpson's diversity index
- Test edge cases: single category, all categories equally represented
- Test handling of zero-count categories
- Property test: diversity increases with more evenly distributed categories

**Logsum (`math/logsum.py`):**

- Already at 94.12%, but add missing edge case:
- Test extreme utility differences (Umax - Umin > 100)
- Test nest structure with degenerate nests (single mode per nest)

**GTC (Generalized Travel Cost) (`math/gtc.py`):**

- Already at 100%, maintain coverage with regression tests

### Testing Strategy

**Property-Based Testing with Hypothesis:**

- Use `@given` decorators to generate random valid inputs
- Test mathematical invariants that must hold for all inputs:
  - **Monotonicity**: If x1 ≤ x2 component-wise, then f(x1) ≤ f(x2)
  - **Homogeneity**: f(k·x) = k^α · f(x) for appropriate α
  - **Bounds**: 0 ≤ f(x) ≤ max(x) for normalized functions
  - **Continuity**: Small input changes → small output changes (Lipschitz continuity)

**Edge Case Testing:**

- Zero inputs: f(0, 0, ..., 0)
- Single non-zero input: f(x, 0, 0, ...)
- All equal inputs: f(x, x, x, ...)
- Extreme values: f(1e-10, 1e10)
- Pathological distributions: f(1e6, 1, 1, ..., 1)

**Numerical Stability Testing:**

- Test with `numpy.finfo(float64)` limits
- Test intermediate overflow/underflow detection
- Test loss of precision with very large or very small numbers

**Regression Testing:**

- Store known input-output pairs from production runs
- Ensure code changes don't alter results for historical inputs
- Use `pytest.approx` with appropriate tolerances (rtol=1e-6 for math functions)

### Coverage Targets

- `math/ces.py`: 78.95% → 95%
- `math/diversity.py`: 79.78% → 95%
- `math/satiation.py`: 34.48% → 95%
- `math/logsum.py`: 94.12% → 98%
- **Overall `math` module: 81.69% → 95%+**

## Impact

**Affected specs:**

- `specs/testing/spec.md` (add mathematical property testing requirements)
- `specs/essentials-access/spec.md` (clarify satiation behavior)
- `specs/leisure-culture-access/spec.md` (document CES parameter constraints)

**Affected code:**

- `src/Urban_Amenities2/math/` (test additions only, no production code changes)
- New test files in `tests/math/` (expand existing tests)
- Shared fixtures in `tests/fixtures/math_samples.py` for regression test vectors

**Benefits:**

- Increased confidence in score calculation correctness
- Earlier detection of numerical instability issues
- Documented expected behavior through executable tests
- Protection against regressions when refactoring math functions

**Risks:**

- Property-based tests can be slow (mitigate with `@settings(max_examples=100)`)
- False positives from floating-point precision (mitigate with appropriate `rtol` in assertions)
- Over-testing may slow down test suite (focus on critical paths first)

**Migration:**

- No production code changes
- Existing tests remain unchanged
- New tests added to expand coverage
- No breaking changes to function signatures or behaviors
