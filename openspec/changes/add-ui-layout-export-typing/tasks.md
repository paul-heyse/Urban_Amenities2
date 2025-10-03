## 1. Baseline & Planning
- [ ] 1.1 Collect mypy errors for `ui/export.py`, layout export handlers, and tests
- [ ] 1.2 Identify export payload shapes (GeoJSON features, CSV rows, shapefile metadata)

## 2. Export Typing
- [ ] 2.1 Annotate export functions with precise types (TypedDict/dataclasses for features, properties)
- [ ] 2.2 Introduce typed helper utilities for geometry conversion (centroids, WKT)
- [ ] 2.3 Add typed wrapper around Dash file response helper (stand-in for `dcc.send_file`)

## 3. Layout Integration
- [ ] 3.1 Update layouts/callbacks invoking exports to use typed helpers
- [ ] 3.2 Ensure typed error handling and logging in export flows

## 4. Tests & Docs
- [ ] 4.1 Expand tests to validate typed export outputs (GeoJSON structure, CSV columns)
- [ ] 4.2 Document export typing patterns in developer guide
- [ ] 4.3 Run mypy on export modules/layouts; resolve all errors without suppressions

## 5. Validation
- [ ] 5.1 Smoke test export endpoints via pytest UI tests
- [ ] 5.2 Capture before/after mypy reports for change record
- [ ] 5.3 Submit for review and archive change upon approval
