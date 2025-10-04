## Why
Even with typed data context and components, the export utilities (`ui/export.py`) and layout-specific logic (e.g., map export to CSV/GeoJSON, overlays) still use dynamic data structures and lack type annotations. Mypy highlights type mismatches for export outputs, Dash send_file usage, and layout-specific context. To complete UI type safety, we must annotate export paths, file response helpers, and layout-specific state interactions.

## What Changes
- Annotate `ui/export.py` functions (GeoJSON/CSV/shapefile export) and ensure typed return values and parameters.
- Replace dynamic dict/list manipulations with typed structures for exported features, geometry conversions, and file metadata.
- Update layout-level helpers that invoke exports (e.g., map view export buttons) to ensure typed interactions with Dash send_file equivalents.
- Introduce typed wrappers for file response helpers (Dash `dcc.send_file` fallback) to avoid attr-defined errors.
- Ensure mypy passes across export modules and layout export code without suppressions.
- Extend tests to validate typed export payloads and verify compatibility with typed data context.

## Impact
- Affected specs: `frontend/ui`, `qa/type-safety`
- Affected code: `src/Urban_Amenities2/ui/export.py`, layout modules using exports, UI tests, documentation.
