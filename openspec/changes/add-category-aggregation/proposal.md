# Category Aggregation with CES and Satiation

## Why

Individual amenity scores must be aggregated within categories (e.g., all grocery stores → grocery category score). Simple averaging treats amenities as perfect substitutes; CES model captures imperfect substitution, and satiation models diminishing returns.

## What Changes

- Implement CES aggregation (E10) with elasticity ρ_c per category
- Implement satiation curves (E11-E12): S_c = 100 · (1 - exp(-κ_c · V_c))
- Compute κ_c from anchor reference points (e.g., 5 groceries → 80% satiated)
- Within-category diversity bonuses (E13) for variety (e.g., mix of grocery types)

## Impact

- Affected specs: `category-aggregation` (new)
- Affected code: New `src/Urban_Amenities2/math/ces.py`, `satiation.py`, `diversity.py`
- Dependencies: Requires `add-amenity-quality`, `add-travel-time-computation`
- Mathematical: Implements E10-E13
