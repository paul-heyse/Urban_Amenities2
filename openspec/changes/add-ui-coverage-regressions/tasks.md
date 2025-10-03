## 1. DataContext Coverage
- [ ] 1.1 Add pytest coverage for score dataset discovery (multiple files, missing scores, metadata fallbacks).
- [ ] 1.2 Test overlay generation with and without shapely installed, ensuring warning paths are exercised.
- [ ] 1.3 Cover viewport filtering, aggregation caching, and geometry attachment helpers.

## 2. Layout & Callback Coverage
- [ ] 2.1 Write integration tests for `register_layouts` to assert page registration and component wiring.
- [ ] 2.2 Mock Dash callbacks to capture GeoJSON export payloads and verify overlay opacity/hover columns.
- [ ] 2.3 Cover `ui.performance` helpers (timers, formatting) and `ui.downloads.send_file` responses.

## 3. Regression Harness
- [ ] 3.1 Build reusable UI fixtures (datasets, overlays, settings) to keep tests deterministic.
- [ ] 3.2 Ensure UI coverage suites run in CI and update docs describing how to execute them locally.
