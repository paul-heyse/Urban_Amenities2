# Implementation Tasks: Add Math Module Test Coverage

## 1. Test Infrastructure Setup

- [ ] 1.1 Verify `hypothesis` is installed: `micromamba list | grep hypothesis`
- [ ] 1.2 If missing, install: `micromamba install -p ./.venv -c conda-forge hypothesis`
- [ ] 1.3 Create `tests/fixtures/math_samples.py` for regression test vectors
- [ ] 1.4 Define shared property test strategies in `tests/math/strategies.py`

## 2. CES Aggregation Testing (High Priority)

- [ ] 2.1 Extend `tests/test_math.py` or create `tests/math/test_ces_extended.py`
  - [ ] Test Cobb-Douglas limit (ρ → 0): verify log-transform behavior
  - [ ] Test linear aggregation (ρ = 1): verify output = mean(inputs)
  - [ ] Test complementary goods (ρ < 0): verify output < min(inputs)
  - [ ] Test near-perfect substitutes (ρ > 10): verify output ≈ max(inputs)
  - [ ] Test overflow handling: inputs = [1e300, 1e300, 1e300], ρ = 2
  - [ ] Test underflow handling: inputs = [1e-300, 1e-300], ρ = 2
  - [ ] Property test monotonicity: `@given(st.lists(st.floats(min_value=0, max_value=1e6), min_size=2))`
  - [ ] Property test homogeneity: scale inputs by k, verify output scales by k^(1/ρ)
  - [ ] Property test bounds: output ≤ max(inputs) when ρ > 0

## 3. Satiation Function Testing (High Priority - Currently 34.48%)

- [ ] 3.1 Create `tests/math/test_satiation.py`
  - [ ] Test core formula: `w(n) = (1 - exp(-λ*n)) / n` for n > 0
  - [ ] Test λ sensitivity:
    - [ ] λ = 0.1 (weak satiation): w(10) ≈ 0.063
    - [ ] λ = 1.0 (medium satiation): w(10) ≈ 0.000045
    - [ ] λ = 5.0 (strong satiation): w(10) ≈ 0.0 (effectively saturated)
  - [ ] Test n = 0 handling: should raise ValueError or return NaN with warning
  - [ ] Test n = 1 trivial case: w(1) = 1 - exp(-λ)
  - [ ] Test large n asymptote: lim(n→∞) w(n) = 0
  - [ ] Test vectorized operation: input array [1, 2, 5, 10], verify element-wise satiation
  - [ ] Property test monotonicity: w(n1) > w(n2) when n1 < n2
  - [ ] Test negative n handling: should raise ValueError
  - [ ] Test array with mix of valid and edge case values

## 4. Diversity Bonus Testing (Medium Priority)

- [ ] 4.1 Extend `tests/test_math.py` or create `tests/math/test_diversity_extended.py`
  - [ ] Test uniform distribution: [10, 10, 10] → diversity = 1.0
  - [ ] Test skewed distribution: [100, 1, 1] → diversity < 0.5
  - [ ] Test single category: [50] → diversity = 0.0 (no diversity)
  - [ ] Test entropy-based metric: verify H(p) = -Σ(p_i * log(p_i))
  - [ ] Test Simpson's diversity: D = 1 - Σ(p_i^2)
  - [ ] Test zero-count categories: [10, 0, 0, 5] → exclude zeros from calculation
  - [ ] Property test: diversity increases with more evenly distributed counts
  - [ ] Test edge case: all zeros → diversity = 0.0 or undefined (document choice)

## 5. Logsum Testing (Low Priority - Already 94.12%)

- [ ] 5.1 Add missing edge case to `tests/test_math.py`
  - [ ] Test extreme utility differences: Umax - Umin > 100 (exp overflow risk)
  - [ ] Test degenerate nest: single mode per nest (logsum = utility)
  - [ ] Test negative utilities: ensure correct handling (should work but verify)

## 6. Property-Based Testing with Hypothesis

- [ ] 6.1 Define reusable strategies in `tests/math/strategies.py`:

  ```python
  from hypothesis import strategies as st

  # Positive floats for counts/weights
  positive_floats = st.floats(min_value=1e-6, max_value=1e6, allow_nan=False, allow_infinity=False)

  # Small positive floats for elasticity parameters
  elasticity_params = st.floats(min_value=-5.0, max_value=10.0, exclude_min=False)

  # Lists of positive values for CES inputs
  ces_inputs = st.lists(positive_floats, min_size=2, max_size=20)

  # Satiation lambda parameters
  satiation_lambdas = st.floats(min_value=0.01, max_value=10.0)

  # Amenity counts for satiation
  amenity_counts = st.integers(min_value=1, max_value=1000)
  ```

- [ ] 6.2 Implement property tests for CES:

  ```python
  from hypothesis import given, settings

  @given(inputs=ces_inputs, rho=elasticity_params)
  @settings(max_examples=100, deadline=1000)  # 100 examples, 1s per test
  def test_ces_monotonicity(inputs, rho):
      result1 = ces_aggregate(inputs, rho)
      inputs_scaled = [x * 1.1 for x in inputs]
      result2 = ces_aggregate(inputs_scaled, rho)
      assert result2 >= result1, "CES must be monotonic"
  ```

- [ ] 6.3 Implement property tests for satiation:

  ```python
  @given(n1=amenity_counts, n2=amenity_counts, lambda_param=satiation_lambdas)
  @settings(max_examples=100)
  def test_satiation_monotonicity(n1, n2, lambda_param):
      if n1 < n2:
          w1 = satiation_weight(n1, lambda_param)
          w2 = satiation_weight(n2, lambda_param)
          assert w1 > w2, f"Satiation must decrease with more amenities: w({n1})={w1} > w({n2})={w2}"
  ```

## 7. Numerical Stability Testing

- [ ] 7.1 Create `tests/math/test_numerical_stability.py`
  - [ ] Test CES with extreme values:
    - [ ] inputs = [np.finfo(np.float64).max, np.finfo(np.float64).max] → should not overflow
    - [ ] inputs = [np.finfo(np.float64).tiny, np.finfo(np.float64).tiny] → should not underflow
  - [ ] Test satiation with very large n:
    - [ ] n = 10^6, λ = 1.0 → w(n) should be effectively zero (< 1e-10)
  - [ ] Test logsum with extreme utilities:
    - [ ] utilities = [1000, 1001, 1002] → should use log-sum-exp trick
  - [ ] Test loss of precision scenarios:
    - [ ] CES with inputs differing by 10+ orders of magnitude

## 8. Regression Testing with Known Vectors

- [ ] 8.1 Define regression test vectors in `tests/fixtures/math_samples.py`:

  ```python
  CES_REGRESSION_VECTORS = [
      # (inputs, rho, expected_output, rtol)
      ([10.0, 20.0, 30.0], 2.0, 22.803508502, 1e-6),
      ([5.0, 5.0, 5.0], 1.0, 5.0, 1e-10),  # Linear case
      ([100.0, 1.0, 1.0], 0.5, 34.142135624, 1e-6),
  ]

  SATIATION_REGRESSION_VECTORS = [
      # (n, lambda, expected_weight, rtol)
      (1, 1.0, 0.632120559, 1e-6),
      (5, 0.5, 0.164023457, 1e-6),
      (10, 2.0, 0.0000002061, 1e-6),
  ]
  ```

- [ ] 8.2 Implement regression tests:

  ```python
  import pytest
  from tests.fixtures.math_samples import CES_REGRESSION_VECTORS

  @pytest.mark.parametrize("inputs,rho,expected,rtol", CES_REGRESSION_VECTORS)
  def test_ces_regression(inputs, rho, expected, rtol):
      result = ces_aggregate(inputs, rho)
      assert result == pytest.approx(expected, rel=rtol)
  ```

## 9. Edge Case Documentation

- [ ] 9.1 Create `tests/math/README.md` documenting:
  - Expected behavior for edge cases (n=0, ρ→0, empty inputs, etc.)
  - Numerical stability guarantees and limitations
  - Floating-point precision expectations (rtol=1e-6 for most tests)
  - Property testing coverage and interpretation

## 10. Verification & Coverage Check

- [ ] 10.1 Run math module tests with coverage: `pytest tests/math/ -v --cov=src/Urban_Amenities2/math --cov-report=term-missing`
- [ ] 10.2 Verify each submodule meets target:
  - [ ] `math/ces.py`: ≥95%
  - [ ] `math/satiation.py`: ≥95%
  - [ ] `math/diversity.py`: ≥95%
  - [ ] `math/logsum.py`: ≥98%
- [ ] 10.3 Run property tests with verbose output to verify invariants
- [ ] 10.4 Verify overall `math` module coverage ≥95%
