## 1. Implementation
- [ ] 1.1 Update `compute_z` to coerce quality and accessibility inputs to float64 within the numba-safe path.
- [ ] 1.2 Adjust Essentials Access aggregation to reuse the sanitized arrays and maintain empty-category safeguards.
- [ ] 1.3 Extend unit/CLI tests covering `compute_z`, EA scoring, and the `score ea` CLI path to guard against dtype regressions.
- [ ] 1.4 Run `pytest -q` (with coverage) and ensure thresholds still pass.
