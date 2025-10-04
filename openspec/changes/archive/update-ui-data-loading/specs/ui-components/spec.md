## ADDED Requirements

### Requirement: Slider Tooltip Typing Support
UI component helpers SHALL expose a typed `SliderTooltip` alias so parameter panels can configure dash sliders without import errors.

#### Scenario: Filters import slider tooltip
- **WHEN** `build_filter_panel` imports `SliderTooltip`
- **THEN** the alias SHALL resolve from `Urban_Amenities2.ui.types` without raising `ImportError`.

#### Scenario: Tooltip structure declared
- **WHEN** developers construct slider tooltips for weight sliders
- **THEN** the alias SHALL describe at least the `placement` and `always_visible` keys so mypy and IDEs can validate usage.
