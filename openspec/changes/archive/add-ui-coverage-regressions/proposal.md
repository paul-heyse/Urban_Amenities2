## Why
The UI stack (data loader, callbacks, layouts, exports, performance helpers) contributes heavily to the current coverage deficit. We need structured regression tests that exercise these modules end-to-end so the new 85% UI coverage bar is achievable.

## What Changes
- Add focused tests for `DataContext` dataset discovery, overlay generation, and error handling.
- Exercise Dash callbacks, layouts, and export helpers through integration-style pytest suites.
- Cover utility modules (`ui.performance`, `ui.downloads`, `ui.layers`) with deterministic fixtures.

## Impact
- Affected specs: testing
- Affected code: `tests/test_ui_*`, potential new fixtures under `tests/ui_factories.py`, UI helper modules under `src/Urban_Amenities2/ui`
