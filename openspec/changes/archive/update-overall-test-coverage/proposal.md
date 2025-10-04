## Why
Overall line coverage sits around 72–73%, and partial test runs collapse due to the global 95% gate being unmet. We need a higher baseline across core packages and an explicit plan to reach ≥95% aggregate coverage so the gate can pass reliably in CI.

## What Changes
- Raise the “Unit Test Coverage” requirement to mandate ≥95% overall coverage, with minimums for math, routing, and UI modules.
- Require coverage enforcement to run via pytest and fail builds that fall below the thresholds.
- Document measurement steps and integrate them with the existing coverage gate.

## Impact
- Affected specs: testing
- Affected code: `.coveragerc`, coverage CI configuration, pytest invocation scripts
