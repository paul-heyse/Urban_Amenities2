# Category Aggregation Implementation Tasks

## 1. CES Aggregation (12 tasks)

- [ ] 1.1 Create `src/Urban_Amenities2/math/ces.py` module
- [ ] 1.2 Implement CES formula: V_c = (Σ(w_ia * Q_a)^ρ_c)^(1/ρ_c) (E10)
- [ ] 1.3 Load elasticity parameters ρ_c per category from params.yaml
- [ ] 1.4 Handle ρ → 0 case (Cobb-Douglas limit)
- [ ] 1.5 Handle ρ → 1 case (linear aggregation)
- [ ] 1.6 Validate ρ_c ranges (-∞ < ρ < 1, typically [0, 0.9])
- [ ] 1.7 Implement numerically stable computation (avoid overflow)
- [ ] 1.8 Test with varying ρ values (check substitution behavior)
- [ ] 1.9 Optimize performance with NumPy vectorization
- [ ] 1.10 Add logging for CES computation (input counts, output values)
- [ ] 1.11 Unit test CES with synthetic data
- [ ] 1.12 Property test: monotonicity (more amenities → higher V_c)

## 2. Satiation Curves (10 tasks)

- [ ] 2.1 Create `src/Urban_Amenities2/math/satiation.py` module
- [ ] 2.2 Implement satiation formula: S_c = 100 · (1 - exp(-κ_c · V_c)) (E11)
- [ ] 2.3 Compute κ_c from anchor points (E12): κ_c = -ln(1 - S_anchor/100) / V_anchor
- [ ] 2.4 Load anchor definitions per category from params.yaml (e.g., 5 groceries → 80 points)
- [ ] 2.5 Validate κ_c > 0 (satiation must increase with V_c)
- [ ] 2.6 Test satiation curves (verify asymptotic behavior → 100)
- [ ] 2.7 Test with extreme cases (V_c=0 → S_c=0, V_c→∞ → S_c=100)
- [ ] 2.8 Visualize satiation curves for all categories (optional QA)
- [ ] 2.9 Unit test satiation with known anchor points
- [ ] 2.10 Property test: S_c in [0, 100]

## 3. Diversity Bonuses (8 tasks)

- [ ] 3.1 Create `src/Urban_Amenities2/math/diversity.py` module
- [ ] 3.2 Implement Shannon diversity index for subcategories (E13)
- [ ] 3.3 Identify subcategories per category (e.g., grocery types: supermarket, specialty, organic)
- [ ] 3.4 Compute diversity score: H = -Σ(p_i · ln(p_i)) where p_i = proportion of subcategory i
- [ ] 3.5 Normalize diversity to bonus multiplier (1.0-1.2×)
- [ ] 3.6 Apply diversity bonus to category score
- [ ] 3.7 Test with monoculture (all same type) vs diverse mix
- [ ] 3.8 Unit test diversity computation

## 4. Integration and Testing (5 tasks)

- [ ] 4.1 Integrate CES, satiation, diversity into accessibility pipeline
- [ ] 4.2 Run full pipeline with aggregation on test dataset (100 hexes)
- [ ] 4.3 Validate output: category scores in [0, 100]
- [ ] 4.4 Compare with/without aggregation (verify impact)
- [ ] 4.5 Document aggregation parameters and tuning guidance
