## ADDED Requirements
### Requirement: Routing Services Type Safety
Routing clients, monitoring collectors, and CLI exports SHALL expose typed interfaces that mypy can fully validate.

#### Scenario: Typed OSRM client interactions
- **WHEN** `mypy src/Urban_Amenities2/router --warn-unused-ignores` is executed
- **THEN** OSRM clients SHALL pass with zero errors, using typed request params, typed response structures, and no implicit `Any` conversions.

#### Scenario: Typed monitoring metrics
- **WHEN** metrics and health checks accumulate routing statistics
- **THEN** collectors SHALL rely on typed containers (no unions requiring runtime coercion)
- **AND** aggregation helpers SHALL return `None` or well-defined numeric types without `Any` fallbacks.

#### Scenario: CLI export correctness
- **WHEN** `aucs export` generates GeoJSON
- **THEN** sanitised properties SHALL be typed as `dict[str, object]`
- **AND** type checks SHALL confirm no implicit union widening occurs in CLI helpers.
