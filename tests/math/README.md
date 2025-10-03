# Math Test Coverage Notes

This directory collects extended regression and property-based tests for the
`Urban_Amenities2.math` package. The tests document the expected behaviour and
numerical tolerances for critical kernels.

- **Tolerance conventions**: Unless otherwise stated, assertions use a relative
tolerance of `1e-6` for CES and diversity routines and combine relative and
absolute tolerances for satiation weights where values approach zero.
- **Edge cases**: Inputs of zero are rejected for satiation weights, elasticities
beyond `MAX_RHO = 10` raise `ValueError`, and CES aggregation guards against
overflow by scaling values before exponentiation.
- **Numerical stability**: Regression tests exercise values near
`np.finfo(float64).max` and `np.finfo(float64).tiny` to ensure kernels remain
finite. Log-sum-exp calculations are validated with utilities separated by more
than 100 points to confirm the stabilisation logic.
- **Property-based testing**: Hypothesis strategies in
`tests/math/strategies.py` generate positive floats in the range `[1e-6, 1e6]`
and elasticity parameters `[-5, 10]`. Monotonicity, homogeneity, and bounds are
verified for CES, while satiation weights are checked for strict decreases as
counts grow.

Use `pytest tests/math -v` or `pytest tests/math --maxfail=1 --disable-warnings`
with coverage flags (`--cov=src/Urban_Amenities2/math`) to validate these
expectations when touching the math module.
