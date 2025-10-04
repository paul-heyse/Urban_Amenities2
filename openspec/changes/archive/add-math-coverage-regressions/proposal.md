## Why
Core math and scoring modules (CES, logsums, accessibility, scoring aggregation) currently have minimal coverage, making the 90% math target unreachable and allowing regressions to slip through. We need targeted property-based and regression tests that lock down expected behaviour.

## What Changes
- Add unit and property-based tests for CES/logsum/aggregation functions, including edge cases that previously triggered numba errors.
- Cover scoring pipelines (essentials access, normalisation, penalties) with deterministic fixtures to validate numeric outputs.
- Introduce snapshot comparisons for key scoring functions to guard against accidental behavioural drift.

## Impact
- Affected specs: testing
- Affected code: `tests/test_math.py`, `tests/test_scores.py`, supporting fixtures, math utilities under `src/Urban_Amenities2/math` and `src/Urban_Amenities2/scores`
