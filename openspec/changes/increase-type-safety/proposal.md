## Why
The codebase currently relies on numerous `# type: ignore` suppressions and incomplete annotations, preventing mypy from detecting inconsistencies. Removing the suppressions during an exploratory run surfaced 170+ typing errors across ingestion, routing, scoring, and UI modules. Without a structured effort, type regressions will persist, reducing developer confidence and allowing latent bugs to slip through.

## What Changes
- Establish a type-safety initiative targeting zero `# type: ignore` suppressions (apart from vetted third-party boundary cases) and a clean mypy run.
- Add/strengthen type annotations across modules, refactoring patterns that block precise typing (e.g., dynamic attribute bags, implicit Any usage).
- Provide typed facades or adapters for external libraries lacking stubs (pandas, geopandas, shapely, plotly, diskcache, etc.), installing community stub packages where available.
- Integrate mypy (with strict per-module configuration) into CI to prevent regressions, including enforcing `warn_unused_ignores`.
- Update contributor documentation with typing guidelines, common patterns, and stub management instructions.

## Impact
- Affected specs: `qa/type-safety`
- Affected code: Broad swaths of `src/Urban_Amenities2/`, test fixtures where signature changes ripple, tooling (CI, pre-commit, developer docs).
