## ADDED Requirements

### Requirement: UI Regression Coverage
The UI platform SHALL provide regression tests that exercise data loading, layout rendering, and export flows to sustain the 85% coverage target.

#### Scenario: DataContext regression suite
- **WHEN** running `pytest tests/test_ui_data_loader.py`
- **THEN** tests SHALL cover dataset discovery, metadata joins, overlay construction (with and without shapely), and error logging paths
- **AND** failures SHALL block the build

#### Scenario: Layout and callback coverage
- **WHEN** running `pytest tests/test_ui_layouts.py`
- **THEN** Dash layouts and callbacks SHALL be executed to validate component registration, overlay payloads, and export callbacks without raising exceptions

#### Scenario: UI helper coverage
- **WHEN** running `pytest tests/test_ui_components_structure.py tests/test_ui_export.py`
- **THEN** utility helpers (`ui.performance`, `ui.downloads`, `ui.layers`, export builders) SHALL have deterministic tests that verify their outputs and increase coverage for the UI package
