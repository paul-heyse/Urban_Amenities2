## ADDED Requirements
### Requirement: Typed UI Data Context
The UI data loading and geometry caching layer SHALL provide explicit type definitions for scores, metadata, geometry cache entries, and overlay payloads, ensuring mypy passes without suppressions.

#### Scenario: Typed geometry cache interactions
- **WHEN** a developer uses `HexGeometryCache`
- **THEN** method signatures and return types are fully annotated, enabling static type checking of STRtree queries and geometry retrievals

#### Scenario: Typed overlay payloads
- **WHEN** overlay GeoJSON payloads are constructed
- **THEN** TypedDict/dataclass helpers define the structure, and mypy confirms typed usage

#### Scenario: Documentation support
- **WHEN** contributors consult UI documentation
- **THEN** they find guidance on typed data loaders, geometry cache usage, and overlay typing patterns
