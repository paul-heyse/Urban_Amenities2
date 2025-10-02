## 1. CES Aggregation Implementation

- [ ] 1.1 Create `src/Urban_Amenities2/math/ces.py` with:
  - [ ] 1.1.1 CES aggregator function: V_c = (Σ z_{i,a})^(1/ρ_c) where z = (Q_a · w_{i,a})^ρ_c
  - [ ] 1.1.2 Handle edge cases: empty categories, zero weights, numerical precision
  - [ ] 1.1.3 Vectorized implementation for all hexes × categories
  - [ ] 1.1.4 Add Numba JIT decoration for performance
- [ ] 1.2 Write comprehensive tests for CES aggregation
  - [ ] 1.2.1 Unit tests: known inputs → expected outputs
  - [ ] 1.2.2 Property tests: monotonicity, homogeneity, elasticity
  - [ ] 1.2.3 Edge case tests: single POI, zero accessibility, extreme elasticities

## 2. Satiation Curve Implementation

- [ ] 2.1 Implement satiation function in `src/Urban_Amenities2/math/satiation.py`:
  - [ ] 2.1.1 S_c = 100 · (1 - exp(-κ_c · V_c)) per equation E12
  - [ ] 2.1.2 Anchor-based κ computation: κ = -ln(1 - S_target/100) / V_target
  - [ ] 2.1.3 Support both fixed and anchor-based κ from config
  - [ ] 2.1.4 Vectorize across categories
- [ ] 2.2 Write tests for satiation
  - [ ] 2.2.1 Verify asymptotic approach to 100
  - [ ] 2.2.2 Validate anchor matching (V_target → S_target)
  - [ ] 2.2.3 Test numerical stability for large V_c

## 3. Within-Category Diversity

- [ ] 3.1 Create `src/Urban_Amenities2/math/diversity.py` with:
  - [ ] 3.1.1 Shannon entropy: H_c = -Σ p_{c,g} ln(p_{c,g}) where p = Q-weighted shares by subtype
  - [ ] 3.1.2 Diversity bonus: DivBonus_c = υ_c · (e^H_c - 1)
  - [ ] 3.1.3 Apply per-category caps from config (default 5 points)
  - [ ] 3.1.4 Handle single-type categories (H=0)
- [ ] 3.2 Define subtype groupings for essential categories:
  - [ ] 3.2.1 Groceries: supermarket, specialty, farmers market, ethnic
  - [ ] 3.2.2 Healthcare: clinic, urgent care, hospital, dental
  - [ ] 3.2.3 Use aucstype and brand as subtype discriminators
- [ ] 3.3 Write tests for diversity computation

## 4. Shortfall Penalty

- [ ] 4.1 Implement shortfall penalty in `src/Urban_Amenities2/scores/penalties.py`:
  - [ ] 4.1.1 Count categories below S_min threshold (default 20 points)
  - [ ] 4.1.2 Apply per-miss penalty (default 2 points per category)
  - [ ] 4.1.3 Cap total penalty at P_max (default 8 points)
  - [ ] 4.1.4 Per equation E15
- [ ] 4.2 Write tests for penalty logic
  - [ ] 4.2.1 Test penalty accumulation
  - [ ] 4.2.2 Verify cap enforcement
  - [ ] 4.2.3 Test edge cases (all categories good, all categories bad)

## 5. EA Subscore Composition

- [ ] 5.1 Create `src/Urban_Amenities2/scores/essentials_access.py` with main EA function:
  - [ ] 5.1.1 Load POIs and accessibility weights for essential categories
  - [ ] 5.1.2 For each hex, compute z_{i,a} = (Q_a · w_{i,a})^ρ_c for all amenities
  - [ ] 5.1.3 Apply CES aggregation per category → V_c
  - [ ] 5.1.4 Apply satiation → S_c per category
  - [ ] 5.1.5 Compute diversity bonus per category
  - [ ] 5.1.6 Take mean across essential categories
  - [ ] 5.1.7 Subtract shortfall penalty → final EA(i) per equation E14
- [ ] 5.2 Implement batch processing for large hex sets
- [ ] 5.3 Add progress logging and performance metrics
- [ ] 5.4 Write integration tests for full EA pipeline

## 6. Explainability and Attribution

- [ ] 6.1 For each hex, identify top-K contributing POIs per essential category:
  - [ ] 6.1.1 Rank by z_{i,a} = (Q_a · w_{i,a})^ρ_c
  - [ ] 6.1.2 Store top 3-5 with poi_id, name, aucstype, contribution value
- [ ] 6.2 Compute category-level contributions to EA score
- [ ] 6.3 Generate explainability JSON structure
- [ ] 6.4 Write explainability to output alongside scores

## 7. Data Quality and Validation

- [ ] 7.1 Add Pandera schema for EA output:
  - [ ] 7.1.1 hex_id, EA (0-100), category_scores dict, contributors dict
  - [ ] 7.1.2 Validate EA is in valid range
  - [ ] 7.1.3 Check for NaN/inf values
- [ ] 7.2 Implement invariant checks:
  - [ ] 7.2.1 EA ≥ 0 and EA ≤ 100 (with penalty, can go slightly negative but should floor at 0)
  - [ ] 7.2.2 Category scores approach but don't exceed 100
  - [ ] 7.2.3 Higher CES inputs → higher or equal outputs (monotonicity)
- [ ] 7.3 Create quality report for EA distribution

## 8. Parameter Sensitivity and Calibration

- [ ] 8.1 Create calibration utilities in `src/Urban_Amenities2/calibration/`:
  - [ ] 8.1.1 Sensitivity analysis for ρ_c, κ_c, diversity weights
  - [ ] 8.1.2 Visualizations of category score distributions
  - [ ] 8.1.3 Comparison of anchor-based vs fixed satiation
- [ ] 8.2 Generate calibration reports for default parameters
- [ ] 8.3 Document recommended parameter ranges in docs

## 9. CLI Integration

- [ ] 9.1 Add `aucs score ea --run-id <id>` command
- [ ] 9.2 Add `aucs score ea --hex <hex_id>` for single-hex debugging
- [ ] 9.3 Add `aucs calibrate ea --param <param_name> --range <min,max>` for sensitivity
- [ ] 9.4 Write tests for CLI commands

## 10. Documentation

- [ ] 10.1 Write `docs/subscores/essentials_access.md` explaining:
  - [ ] 10.1.1 EA subscore purpose and components
  - [ ] 10.1.2 Mathematical formulation (E10-E15 in plain language)
  - [ ] 10.1.3 Essential categories definition
  - [ ] 10.1.4 Parameter tuning guide
  - [ ] 10.1.5 Interpretation and use cases
- [ ] 10.2 Add docstrings to all EA functions
- [ ] 10.3 Create example notebook: `examples/compute_ea.ipynb`
- [ ] 10.4 Update main README with EA subscore status
