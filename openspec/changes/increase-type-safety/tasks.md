## 1. Baseline Inventory
- [ ] 1.1 Enumerate all `# type: ignore` suppressions and categorize by root cause (missing stubs, dynamic patterns, genuine typing gaps)
- [ ] 1.2 Capture current mypy error list with `warn_unused_ignores=true` and document affected modules
- [ ] 1.3 Identify third-party libraries requiring stub packages or custom protocol wrappers

## 2. Infrastructure & Tooling
- [ ] 2.1 Add project-wide mypy configuration (mypy.ini/pyproject) with strict settings (`warn_unused_ignores`, `warn_return_any`, module-specific strictness)
- [ ] 2.2 Install/maintain type stub dependencies (e.g., pandas-stubs, types-geopandas, types-shapely, plotly-stubs)
- [ ] 2.3 Wire mypy into CI (GitHub Actions workflow) with caching and artifact output for developer inspection
- [ ] 2.4 Provide pre-commit hook or make target to run mypy locally

## 3. Module-Level Typing Improvements
- [ ] 3.1 Data layer (ingestion, enrichment, routing): replace dynamic dict usage with TypedDict/Dataclasses, annotate IO boundaries, ensure mocks provide typed interfaces
- [ ] 3.2 Scores & math kernels: remove implicit `Any`, introduce NumPy typing helpers, annotate vectorized utilities
- [ ] 3.3 UI & CLI: add typings for Dash callbacks, typer commands, data loaders; create protocols for Plotly components where stubs unavailable
- [ ] 3.4 Caching, monitoring, utilities: annotate context managers, logger helpers, caching APIs; ensure psutil and diskcache fallbacks are typed
- [ ] 3.5 Tests: adjust fixtures/mocks to comply with typed signatures, add helper factories for typed objects

## 4. Documentation & Onboarding
- [ ] 4.1 Update CONTRIBUTING.md / developer guides with typing standards, stub management instructions, common patterns
- [ ] 4.2 Record examples of before/after patterns (e.g., Pandas DataFrame annotations, typed config objects)

## 5. Validation & Enforcement
- [ ] 5.1 Achieve clean mypy run (no ignores beyond accepted exceptions) across `src/Urban_Amenities2`
- [ ] 5.2 Verify CI gating; ensure failure surfaces in PR checks
- [ ] 5.3 Conduct team walkthrough; archive change after sign-off
