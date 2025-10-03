## 1. Baseline & Planning
- [x] 1.1 Capture current mypy errors for `ui/data_loader.py`, `ui/hexes.py`, `ui/hex_selection.py`
- [x] 1.2 Inventory data structures (scores rows, metadata, overlays, cache entries) needing explicit typing

## 2. Typing Foundations
- [x] 2.1 Create `ui/types.py` with TypedDict/dataclass definitions for scores records, overlay features, geometry cache entries
- [x] 2.2 Annotate `HexGeometryCache` methods & helpers in `ui/hexes.py`; ensure STRtree interactions typed safely
- [x] 2.3 Annotate shapely/h3 imports with guarded typings; replace `dict`/`list` fallbacks with typed equivalents

## 3. DataContext Refactor
- [x] 3.1 Annotate `DataContext` fields and methods (refresh, load_subset, summarise, overlays)
- [x] 3.2 Explicitly type overlay builder logic (`_build_overlays`, `_load_external_overlays`)
- [x] 3.3 Ensure geometry preparation methods return typed DataFrames/Series

## 4. Tests & Tooling
- [x] 4.1 Add unit tests for typed helpers (geometry cache, overlay builder, summarise)
- [x] 4.2 Run mypy on targeted modules; resolve all errors without suppressions
- [x] 4.3 Document typed UI data patterns in developer guide

## 5. Validation
- [x] 5.1 Execute existing UI tests (pytest) to confirm no regressions
- [x] 5.2 Capture before/after mypy diff for change log
- [x] 5.3 Submit for review and archive change upon approval
