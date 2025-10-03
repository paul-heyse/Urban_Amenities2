## Why
After typing the data context, UI components (filters, overlay controls, choropleth builder) and callbacks still rely on loosely typed dicts and implicit Any operations. Mypy surfaces dozens of errors in `ui/components/`, `ui/callbacks.py`, `ui/layers.py`, and `ui/layouts/*.py`. To safely evolve the interactive UI, we need typed props, callback inputs/outputs, and Plotly figure structures.

## What Changes
- Introduce typed helper functions and enums for component options (filters, overlays, score selectors).
- Annotate Dash callback signatures, input/output states, and ensure typed callback decorators.
- Refactor `ui/layers.py` and `ui/components/choropleth.py` to use typed figure constructors (structural typing via dataclasses/TypedDict) instead of raw dicts.
- Update layout factories (`home`, `map_view`, `data_management`, `settings`) to consume typed data context outputs.
- Adjust UI tests to validate typed callbacks and component payloads; add fixtures as necessary.
- Ensure mypy passes for `ui/components`, `ui/layers`, `ui/callbacks`, `ui/layouts` without suppressions.
- Document best practices for typed Dash callbacks.

## Impact
- Affected specs: `frontend/ui`, `qa/type-safety`
- Affected code: `src/Urban_Amenities2/ui/components/*.py`, `ui/callbacks.py`, `ui/layers.py`, layout modules, tests, docs.
