## 1. CES Aggregation Implementation

- [x] 1.1 Create `src/Urban_Amenities2/math/ces.py` with:
  - [x] 1.1.1 CES aggregator function: V_c = (Σ z_{i,a})^(1/ρ_c) where z = (Q_a · w_{i,a})^ρ_c
  - [x] 1.1.2 Handle edge cases: empty categories, zero weights, numerical precision
  - [x] 1.1.3 Vectorized implementation for all hexes × categories
  - [x] 1.1.4 Add Numba JIT decoration for performance
- [x] 1.2 Write comprehensive tests for CES aggregation
  - [x] 1.2.1 Unit tests: known inputs → expected outputs
  - [x] 1.2.2 Property tests: monotonicity, homogeneity, elasticity
  - [x] 1.2.3 Edge case tests: single POI, zero accessibility, extreme elasticities

## 2. Satiation Curve Implementation

- [x] 2.1 Implement satiation function in `src/Urban_Amenities2/math/satiation.py`:
  - [x] 2.1.1 S_c = 100 · (1 - exp(-κ_c · V_c)) per equation E12
  - [x] 2.1.2 Anchor-based κ computation: κ = -ln(1 - S_target/100) / V_target
  - [x] 2.1.3 Support both fixed and anchor-based κ from config
  - [x] 2.1.4 Vectorize across categories
- [x] 2.2 Write tests for satiation
  - [x] 2.2.1 Verify asymptotic approach to 100
  - [x] 2.2.2 Validate anchor matching (V_target → S_target)
  - [x] 2.2.3 Test numerical stability for large V_c

## 3. Within-Category Diversity

- [x] 3.1 Create `src/Urban_Amenities2/math/diversity.py` with:
  - [x] 3.1.1 Shannon entropy: H_c = -Σ p_{c,g} ln(p_{c,g}) where p = Q-weighted shares by subtype
  - [x] 3.1.2 Diversity bonus: DivBonus_c = υ_c · (e^H_c - 1)
  - [x] 3.1.3 Apply per-category caps from config (default 5 points)
  - [x] 3.1.4 Handle single-type categories (H=0)
- [x] 3.2 Define subtype groupings for essential categories:
  - [x] 3.2.1 Groceries: supermarket, specialty, farmers market, ethnic
  - [x] 3.2.2 Healthcare: clinic, urgent care, hospital, dental
  - [x] 3.2.3 Use aucstype and brand as subtype discriminators
- [x] 3.3 Write tests for diversity computation

## 4. Shortfall Penalty

- [x] 4.1 Implement shortfall penalty in `src/Urban_Amenities2/scores/penalties.py`:
  - [x] 4.1.1 Count categories below S_min threshold (default 20 points)
  - [x] 4.1.2 Apply per-miss penalty (default 2 points per category)
  - [x] 4.1.3 Cap total penalty at P_max (default 8 points)
  - [x] 4.1.4 Per equation E15
- [x] 4.2 Write tests for penalty logic
  - [x] 4.2.1 Test penalty accumulation
  - [x] 4.2.2 Verify cap enforcement
  - [x] 4.2.3 Test edge cases (all categories good, all categories bad)

## 5. EA Subscore Composition

- [x] 5.1 Create `src/Urban_Amenities2/scores/essentials_access.py` with main EA function:
  - [x] 5.1.1 Load POIs and accessibility weights for essential categories
  - [x] 5.1.2 For each hex, compute z_{i,a} = (Q_a · w_{i,a})^ρ_c for all amenities
  - [x] 5.1.3 Apply CES aggregation per category → V_c
  - [x] 5.1.4 Apply satiation → S_c per category
  - [x] 5.1.5 Compute diversity bonus per category
  - [x] 5.1.6 Take mean across essential categories
  - [x] 5.1.7 Subtract shortfall penalty → final EA(i) per equation E14
- [x] 5.2 Implement batch processing for large hex sets
- [x] 5.3 Add progress logging and performance metrics
- [x] 5.4 Write integration tests for full EA pipeline

## 6. Explainability and Attribution

- [x] 6.1 For each hex, identify top-K contributing POIs per essential category:
  - [x] 6.1.1 Rank by z_{i,a} = (Q_a · w_{i,a})^ρ_c
  - [x] 6.1.2 Store top 3-5 with poi_id, name, aucstype, contribution value
- [x] 6.2 Compute category-level contributions to EA score
- [x] 6.3 Generate explainability JSON structure
- [x] 6.4 Write explainability to output alongside scores

## 7. Data Quality and Validation

- [x] 7.1 Add Pandera schema for EA output:
  - [x] 7.1.1 hex_id, EA (0-100), category_scores dict, contributors dict
  - [x] 7.1.2 Validate EA is in valid range
  - [x] 7.1.3 Check for NaN/inf values
- [x] 7.2 Implement invariant checks:
  - [x] 7.2.1 EA ≥ 0 and EA ≤ 100 (with penalty, can go slightly negative but should floor at 0)
  - [x] 7.2.2 Category scores approach but don't exceed 100
  - [x] 7.2.3 Higher CES inputs → higher or equal outputs (monotonicity)
- [x] 7.3 Create quality report for EA distribution

## 8. Parameter Sensitivity and Calibration

- [x] 8.1 Create calibration utilities in `src/Urban_Amenities2/calibration/`:
  - [x] 8.1.1 Sensitivity analysis for ρ_c, κ_c, diversity weights
  - [x] 8.1.2 Visualizations of category score distributions
  - [x] 8.1.3 Comparison of anchor-based vs fixed satiation
- [x] 8.2 Generate calibration reports for default parameters
- [x] 8.3 Document recommended parameter ranges in docs

## 9. CLI Integration

- [x] 9.1 Add `aucs score ea --run-id <id>` command
- [x] 9.2 Add `aucs score ea --hex <hex_id>` for single-hex debugging
- [x] 9.3 Add `aucs calibrate ea --param <param_name> --range <min,max>` for sensitivity
- [x] 9.4 Write tests for CLI commands

## 10. Documentation

- [x] 10.1 Write `docs/subscores/essentials_access.md` explaining:
  - [x] 10.1.1 EA subscore purpose and components
  - [x] 10.1.2 Mathematical formulation (E10-E15 in plain language)
  - [x] 10.1.3 Essential categories definition
  - [x] 10.1.4 Parameter tuning guide
  - [x] 10.1.5 Interpretation and use cases
- [x] 10.2 Add docstrings to all EA functions
- [x] 10.3 Create example notebook: `examples/compute_ea.ipynb`
- [x] 10.4 Update main README with EA subscore status
