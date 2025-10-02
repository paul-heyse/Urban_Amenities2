# Essentials Access (EA) Subscore for AUCS 2.0

## Why

The Essentials Access (EA) subscore quantifies how easily residents can reach daily-need amenities like groceries, pharmacies, primary care, childcare, schools, banks, and postal services. This is a core component of urban convenience and accounts for 30% of the final AUCS (highest weight).

EA implements equations E10-E15, including:

- CES aggregation within each essential category
- Satiation curves to prevent runaway returns from many similar options
- Within-category diversity bonuses
- Shortfall penalties when critical categories are poorly served

## What Changes

- Implement CES aggregation for essential categories (E10-E11) with elasticity ρ_c
- Implement satiation curves (E12) using exponential approach to 100-point ceiling
- Compute within-category diversity bonuses (E13) using Shannon entropy on Q-weighted shares
- Apply shortfall penalty (E14-E15) for categories scoring below threshold
- Aggregate essential categories into final EA score
- Generate explainability: top contributing POIs per essential category per hex
- Add EA-specific quality checks and edge case handling
- **BREAKING**: Requires amenity quality (Q_a) and accessibility weights (w_{i,a}) from prior changes

## Impact

- Affected specs: `essentials-access` (new)
- Affected code: Creates `src/Urban_Amenities2/scores/essentials_access.py` with:
  - CES aggregator (E10-E11)
  - Satiation function (E12)
  - Diversity bonus (E13)
  - Shortfall penalty (E14-E15)
  - EA composition function
- Dependencies: None beyond core (uses numpy, scipy)
- Inputs:
  - `data/processed/pois.parquet` (for Q_a and categories)
  - `data/processed/accessibility_poi.parquet` (for w_{i,a})
  - Parameters from `categories.essentials` config
- Outputs: `data/processed/scores_ea.parquet` (hex_id, EA, category_scores, contributors)
