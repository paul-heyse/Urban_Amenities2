# Spec Delta: Math Module Testing Requirements

## ADDED Requirements

### Requirement: Property-Based Mathematical Testing

Mathematical functions SHALL be tested with property-based tests using Hypothesis to verify invariants across the input space.

#### Scenario: CES monotonicity property

- **GIVEN** a CES aggregation function with elasticity ρ
- **WHEN** all inputs are scaled by factor k > 1
- **THEN** the output increases by at least factor k^(1/ρ)
- **AND** the property holds for 100+ randomly generated input vectors

#### Scenario: Satiation monotonicity property

- **GIVEN** a satiation weight function w(n, λ)
- **WHEN** the amenity count n increases
- **THEN** the weight w(n, λ) strictly decreases
- **AND** the property holds for all λ ∈ [0.01, 10] and n ∈ [1, 1000]

### Requirement: Edge Case Coverage

Mathematical functions SHALL explicitly test edge cases including zero inputs, extreme values, and boundary conditions.

#### Scenario: CES with zero inputs

- **GIVEN** a CES aggregation with inputs = [0, 0, 0]
- **WHEN** the function is evaluated
- **THEN** it returns 0.0 without raising an exception

#### Scenario: CES with single non-zero input

- **GIVEN** a CES aggregation with inputs = [42.0, 0, 0]
- **WHEN** the function is evaluated with ρ = 2
- **THEN** it returns 42.0 (single input dominates)

#### Scenario: Satiation with n = 0

- **GIVEN** a satiation weight function with n = 0
- **WHEN** the function is evaluated
- **THEN** it raises `ValueError` with message "n must be positive"

#### Scenario: Satiation large n asymptote

- **GIVEN** a satiation weight function with n = 10^6 and λ = 1.0
- **WHEN** the function is evaluated
- **THEN** the result is < 1e-10 (effectively zero)

### Requirement: Numerical Stability Testing

Mathematical functions SHALL handle extreme values without overflow, underflow, or precision loss.

#### Scenario: CES overflow prevention

- **GIVEN** a CES aggregation with inputs = [1e300, 1e300]
- **WHEN** the function is evaluated with ρ = 2
- **THEN** it returns a finite value without raising `OverflowError`
- **AND** uses stable computation (e.g., scaling before exponentiation)

#### Scenario: Logsum exp overflow protection

- **GIVEN** a logsum with utilities = [1000, 1001, 1002]
- **WHEN** the function is evaluated
- **THEN** it uses the log-sum-exp trick to prevent overflow
- **AND** returns a finite value ≈ 1002 + log(1 + exp(-1) + exp(-2))

#### Scenario: Satiation underflow handling

- **GIVEN** a satiation weight with n = 1000 and λ = 10.0
- **WHEN** exp(-λ*n) underflows to 0.0
- **THEN** the function gracefully handles the underflow
- **AND** returns w(n) ≈ 0.0 without warnings

### Requirement: Regression Test Vectors

Mathematical functions SHALL maintain regression test vectors from production runs to detect unintended behavior changes.

#### Scenario: CES regression vector validated

- **GIVEN** a known CES input: [10.0, 20.0, 30.0] with ρ = 2.0
- **WHEN** the function is evaluated
- **THEN** it returns 22.803508502 ± 1e-6 (relative tolerance)
- **AND** the test fails if the result differs beyond tolerance

#### Scenario: Satiation regression vector validated

- **GIVEN** a known satiation input: n = 5, λ = 0.5
- **WHEN** the function is evaluated
- **THEN** it returns 0.164023457 ± 1e-6
- **AND** the test documents the expected behavior

### Requirement: Elasticity Parameter Coverage

CES aggregation tests SHALL cover the full range of elasticity parameter ρ including limiting cases.

#### Scenario: Cobb-Douglas limit (ρ → 0)

- **GIVEN** a CES aggregation with ρ = 1e-6 (approximating 0)
- **WHEN** the function is evaluated with inputs = [2, 8]
- **THEN** it returns approximately geometric mean: sqrt(2 * 8) = 4.0
- **AND** the result is within 1% of true Cobb-Douglas formula

#### Scenario: Linear aggregation (ρ = 1)

- **GIVEN** a CES aggregation with ρ = 1.0
- **WHEN** the function is evaluated with inputs = [10, 20, 30]
- **THEN** it returns exactly the arithmetic mean: 20.0

#### Scenario: Complementary goods (ρ < 0)

- **GIVEN** a CES aggregation with ρ = -1.0
- **WHEN** the function is evaluated with inputs = [10, 20]
- **THEN** the result is less than min(inputs) = 10
- **AND** reflects strong complementarity (lack of one input hurts total)

#### Scenario: Near-perfect substitutes (ρ = 10)

- **GIVEN** a CES aggregation with ρ = 10.0
- **WHEN** the function is evaluated with inputs = [5, 10, 15]
- **THEN** the result is approximately max(inputs) = 15
- **AND** within 1% of the maximum input

### Requirement: Diversity Metric Testing

Diversity bonus calculations SHALL test uniform, skewed, and degenerate category distributions.

#### Scenario: Uniform distribution maximizes diversity

- **GIVEN** category counts = [10, 10, 10, 10]
- **WHEN** the diversity metric is calculated
- **THEN** it returns the maximum value (1.0 for normalized metrics)

#### Scenario: Skewed distribution reduces diversity

- **GIVEN** category counts = [100, 1, 1, 1]
- **WHEN** the diversity metric is calculated
- **THEN** it returns a value < 0.5 (concentrated distribution)

#### Scenario: Single category has zero diversity

- **GIVEN** category counts = [50]
- **WHEN** the diversity metric is calculated
- **THEN** it returns 0.0 (no diversity)

#### Scenario: Zero-count categories excluded

- **GIVEN** category counts = [10, 0, 0, 5]
- **WHEN** the diversity metric is calculated
- **THEN** only non-zero categories [10, 5] are included
- **AND** zero counts are ignored (not treated as present categories)

### Requirement: Vectorized Operation Testing

Mathematical functions that support array inputs SHALL test vectorized operations for correctness and performance.

#### Scenario: Satiation vectorized over amenity counts

- **GIVEN** an array of amenity counts n = [1, 2, 5, 10]
- **WHEN** the satiation weight function is applied
- **THEN** it returns element-wise results: [w(1), w(2), w(5), w(10)]
- **AND** the vectorized result matches individual evaluations

#### Scenario: CES vectorized over multiple locations

- **GIVEN** a 2D array of inputs (1000 locations × 5 amenity types)
- **WHEN** CES aggregation is applied row-wise
- **THEN** it returns 1000 aggregated scores
- **AND** completes in < 100ms (vectorization performance requirement)

### Requirement: Coverage Thresholds by Module

Math module test coverage SHALL meet or exceed the following thresholds:

- `math/ces.py`: ≥95% line coverage
- `math/satiation.py`: ≥95% line coverage
- `math/diversity.py`: ≥95% line coverage
- `math/logsum.py`: ≥98% line coverage
- `math/gtc.py`: ≥100% line coverage (maintain existing)
- **Overall `math` module: ≥95% line coverage**

#### Scenario: Coverage gate fails for math module regression

- **GIVEN** a pull request modifying `math/satiation.py`
- **WHEN** the CI pipeline runs coverage checks
- **AND** the module coverage drops to 80% (below 95% threshold)
- **THEN** the coverage gate fails
- **AND** the PR is blocked from merging

### Requirement: Floating-Point Precision Documentation

Tests SHALL document expected floating-point precision using relative tolerance (rtol) in assertions.

#### Scenario: CES test uses appropriate tolerance

- **GIVEN** a CES aggregation test with expected result 22.803508502
- **WHEN** the assertion is written
- **THEN** it uses `pytest.approx(expected, rel=1e-6)` for 6 decimal places
- **AND** the tolerance is documented as appropriate for typical inputs

#### Scenario: Satiation test uses stricter tolerance

- **GIVEN** a satiation weight test with small expected result 1e-5
- **WHEN** the assertion is written
- **THEN** it uses `pytest.approx(expected, rel=1e-4, abs=1e-10)` with absolute tolerance
- **AND** handles cases where relative tolerance alone is insufficient
