## ADDED Requirements
### Requirement: Typed UI Components and Callbacks
Dash UI modules SHALL define explicit type annotations for all public functions, layout factories, and callbacks, ensuring the UI package passes mypy checks without suppressions.

#### Scenario: UI mypy target enforced
- **WHEN** CI runs the type-check pipeline
- **THEN** mypy executes against `src/Urban_Amenities2/ui` with project-configured strictness
- **AND** the pipeline FAILS if any UI module emits type errors or unused ignores

#### Scenario: Typed overlay and filter payloads
- **WHEN** a developer constructs overlay payloads or filter option lists
- **THEN** typed helper structures (TypedDict/dataclasses) are used, ensuring IDE tooling and static checks validate data shape

#### Scenario: Contributor guidance
- **WHEN** a contributor updates or adds UI modules
- **THEN** project documentation provides guidelines for typed Dash development, including callback signatures, typed data loaders, and testing strategies
