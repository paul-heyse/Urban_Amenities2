## Why
UI modules (callbacks, map layers, export helpers) currently produce mypy failures—18 errors—involving inconsistent option types, unsafe `None` assignments, and missing Plotly/Dash type information. Without isolating these fixes, front-end regressions risk slipping into production and block the overall type safety initiative.

## What Changes
- Annotate Dash callback inputs/outputs, map layer builders, and export utilities so UI-specific mypy checks pass with `--warn-unused-ignores`.
- Normalize shared helpers (`ui/performance`, `ui/logging`, `ui/hex_selection`) to avoid mutating typed state with `None` and ensure dropdown/trace factories use typed structures.
- Introduce Plotly/Dash-friendly typing patterns (e.g., typed `layers`, custom trace protocols if necessary) and update fixtures/tests to validate behaviour remains unchanged.
- Document UI typing conventions for contributors (dropdown options, map layers, `mapbox_config` construction).

## Impact
- Affected specs: `qa/ui-type-safety`
- Affected code: `src/Urban_Amenities2/ui/*` (callbacks, layouts, layers, export, logging, performance), related tests/fixtures.
