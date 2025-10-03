## 1. Coverage Baseline
- [ ] 1.1 Audit existing pytest/coverage settings and document current module-level coverage outputs.
- [ ] 1.2 Update `.coveragerc` (or equivalent tooling) to track overall and per-package coverage thresholds.

## 2. Enforcement
- [ ] 2.1 Configure pytest invocation to fail when overall coverage drops below 95%.
- [ ] 2.2 Add minimum coverage settings for `src/Urban_Amenities2/math`, `src/Urban_Amenities2/router`, and `src/Urban_Amenities2/ui` as per the updated spec.
- [ ] 2.3 Ensure CI surfaces coverage deltas (e.g., via coverage.xml upload or badge) so regressions are visible.

## 3. Documentation & Verification
- [ ] 3.1 Update developer docs to explain the new coverage targets and how to run the enforcement locally.
- [ ] 3.2 Run the full test suite with coverage enabled and capture artifacts demonstrating thresholds now pass.
