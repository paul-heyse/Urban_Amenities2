## Why
Front-end UI modules (Dash components, layouts, callbacks, data loaders) currently rely on implicit Any typing and lack disciplined interface definitions. That makes refactors risky, obscures expected data shapes, and blocks enforcing mypy across the UI. Dedicated work is needed to introduce explicit type annotations, ensure Plotly/Dash constructs have typed helpers, and eliminate unchecked assumptions about figure payloads and cached data.

## What Changes
- Audit UI modules (`src/Urban_Amenities2/ui/**`) to document untyped entry points, dynamic dict usage, and interactions with cached hex data.
- Introduce typed helper structures (TypedDict/dataclasses) for map overlays, filter controls, and Dash callback inputs/outputs.
- Annotate Dash callbacks, data loader functions, and layout factories to satisfy mypy without depending on protocol facades or stub adapters.
- Update UI tests to exercise typed interfaces (e.g., fixture factories returning typed payloads) and to catch future regressions.
- Ensure mypy/CI incorporate UI modules with strict settings and no residual ignores.
- Document patterns for typed Dash development in developer guides.

## Impact
- Affected specs: `qa/type-safety`, `frontend/ui`
- Affected code: `src/Urban_Amenities2/ui/` modules, UI tests, typing utilities, CI config, developer documentation.
