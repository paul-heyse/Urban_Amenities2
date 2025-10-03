## ADDED Requirements
### Requirement: UI Type Safety Compliance
Urban Amenities UI code SHALL maintain full static type coverage so Dash components, Plotly traces, and helper utilities operate without runtime regressions.

#### Scenario: Clean mypy run for UI modules
- **WHEN** `mypy src/Urban_Amenities2/ui --warn-unused-ignores` is executed
- **THEN** the command SHALL complete with zero errors or unused ignores
- **AND** the output SHALL document no implicit `Any` returns or assignments in UI modules.

#### Scenario: Typed UI configuration builders
- **WHEN** constructing map layers, dropdown options, or export payloads
- **THEN** helper functions SHALL accept/return typed `Mapping`/`Sequence` structures
- **AND** generated values SHALL align with Dash/Plotly expectations without relying on `Any` casts.
