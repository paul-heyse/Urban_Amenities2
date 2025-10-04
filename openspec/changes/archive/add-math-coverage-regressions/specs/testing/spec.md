## ADDED Requirements

### Requirement: Math & Scoring Coverage
Core mathematical kernels and scoring pipelines SHALL maintain deterministic regression tests and property-based checks to sustain the 90% math coverage target.

#### Scenario: CES/logsum regression tests
- **WHEN** running `pytest tests/test_math.py`
- **THEN** tests SHALL cover dtype coercion, rho edge cases, empty inputs, and property-based invariants (monotonicity, homogeneity, bounded outputs)

#### Scenario: Scoring pipeline coverage
- **WHEN** running `pytest tests/test_scores.py`
- **THEN** essentials access, category aggregation, normalisation, and penalty modules SHALL be exercised with deterministic fixtures and snapshot assertions

#### Scenario: Regression guardrails for numba kernels
- **WHEN** executing math/scoring tests under coverage
- **THEN** the numba-compiled paths SHALL be invoked and SHALL guard against regressions such as `'Function' object has no attribute 'dtype'`
