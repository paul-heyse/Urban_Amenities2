## Why
CES aggregation currently raises a numba dtype error (`AttributeError: 'Function' object has no attribute 'dtype'`) when the Essentials Access calculator runs, breaking the EA CLI command and multiple math/scoring tests.

## What Changes
- Harden the `compute_z` CES kernel to coerce numeric inputs to float64 before JIT evaluation.
- Ensure the Essentials Access calculator feeds sanitized float arrays into CES and retains empty-category handling.
- Add regression coverage protecting the CLI EA flow and math invariants against future dtype regressions.

## Impact
- Affected specs: essentials-access
- Affected code: `src/Urban_Amenities2/math/ces.py`, `src/Urban_Amenities2/scores/essentials_access.py`, related tests
