## 1. Implementation
- [x] 1.1 Update `DataContext.refresh` to select the latest score dataset by filename pattern before validating required score columns.
- [x] 1.2 Reinstate a typed `SliderTooltip` definition in `ui.types` and adjust filter/parameter builders if needed.
- [x] 1.3 Extend UI tests to cover dataset selection (ensuring fixtures load) and slider tooltip imports for filter panels.
- [x] 1.4 Run `pytest -q tests/test_ui_layouts.py tests/test_ui_components_structure.py` and confirm coverage gates.
