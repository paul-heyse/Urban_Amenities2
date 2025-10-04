## 1. Baseline & Planning
- [x] 1.1 Collect mypy errors for `ui/export.py`, layout export handlers, and tests
- [x] 1.2 Identify export payload shapes (GeoJSON features, CSV rows, shapefile metadata)

## 2. Export Typing
- [x] 2.1 Annotate export functions with precise types (TypedDict/dataclasses for features, properties)
- [x] 2.2 Introduce typed helper utilities for geometry conversion (centroids, WKT)
- [x] 2.3 Add typed wrapper around Dash file response helper (stand-in for `dcc.send_file`)

## 3. Layout Integration
- [x] 3.1 Update layouts/callbacks invoking exports to use typed helpers
- [x] 3.2 Ensure typed error handling and logging in export flows

## 4. Tests & Docs
- [x] 4.1 Expand tests to validate typed export outputs (GeoJSON structure, CSV columns)
- [x] 4.2 Document export typing patterns in developer guide
- [x] 4.3 Run mypy on export modules/layouts; resolve all errors without suppressions

## 5. Validation
- [x] 5.1 Smoke test export endpoints via pytest UI tests
- [x] 5.2 Capture before/after mypy reports for change record
- [ ] 5.3 Submit for review and archive change upon approval
