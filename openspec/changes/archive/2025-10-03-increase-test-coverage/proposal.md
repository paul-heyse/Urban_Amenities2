## Why
Current automated test coverage is ~73%, leaving critical paths and regression-prone modules insufficiently validated. Raising coverage substantially is required to support upcoming production deployments, reduce defect risk, and comply with internal quality gates.

## What Changes
- Create a comprehensive coverage improvement initiative targeting ≥95% line coverage and ≥90% branch coverage across service layers (data ingestion, routing, scoring, UI, CLI, caching).
- Add missing fixtures, stubs, and integration harnesses to exercise external-service adapters without live dependencies.
- Extend CI workflows to enforce coverage thresholds and track trend reports per pull request.
- Document the expanded testing strategy and update contributor guidance for ongoing maintenance.

## Impact
- Affected specs: `qa/test-quality`
- Affected code: `tests/`, `src/Urban_Amenities2/*` (when instrumentation or minor refactors are required to enable testing), CI workflows, developer docs.
