## 1. CES & Logsum Coverage
- [ ] 1.1 Expand `tests/test_math.py` with cases covering dtype coercion, empty inputs, and rho edge cases.
- [ ] 1.2 Add Hypothesis strategies to verify monotonicity, homogeneity, and bounds for CES and logsum helpers.

## 2. Scoring Pipelines
- [ ] 2.1 Create fixtures for essentials access, category aggregation, and penalties to validate deterministic outputs.
- [ ] 2.2 Cover normalisation and scoring aggregation modules with snapshot assertions to detect behavioural drift.

## 3. Regression Guardrails
- [ ] 3.1 Ensure math/scoring tests exercise the numba JIT path and guard against regressions like the `'Function' object has no attribute 'dtype'` failure.
- [ ] 3.2 Update coverage reporting to confirm `src/Urban_Amenities2/math` and `src/Urban_Amenities2/scores` meet the 90% target.
