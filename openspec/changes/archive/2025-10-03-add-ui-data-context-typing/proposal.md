## Why
`ui/data_loader.py`, `ui/hexes.py`, and related helpers manage the heaviest data plumbing for the Dash interface, yet they remain implicitly typed. Numerous mypy errors stem from untyped DataFrame usage, dynamic dict payloads, and optional shapely/h3 imports. Before annotating callbacks or layouts, we must establish typed foundations for data loading, geometry caching, and overlay generation.

## What Changes
- Introduce explicit typing (TypedDict/dataclasses) for scores data, metadata rows, geometry cache entries, overlay payloads.
- Annotate `DataContext`, `HexGeometryCache`, and helper functions in `ui/data_loader.py` & `ui/hexes.py`, resolving mypy errors without suppressions.
- Create small typed utility modules (e.g., `ui/types.py`) to centralise reusable type aliases.
- Add targeted unit tests ensuring typed helpers behave as expected.
- Update documentation/CONTRIBUTING with guidance for typed UI data handling.
- Ensure mypy run on `ui/data_loader.py` and `ui/hexes.py` succeeds under strict settings.

## Impact
- Affected specs: `frontend/ui`, `qa/type-safety`
- Affected code: `src/Urban_Amenities2/ui/data_loader.py`, `src/Urban_Amenities2/ui/hexes.py`, geometry cache utilities, UI unit tests, typing helpers, documentation.
