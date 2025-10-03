## ADDED Requirements

### Requirement: OSRM Response Compatibility Layer
The routing subsystem SHALL expose OSRM route and table results with dictionary semantics so existing callers can access keys like `"duration"`, `"distance"`, and `"legs"` without adapting to internal dataclass implementations.

#### Scenario: Great-circle fallback emits mapping
- **WHEN** `GreatCircleOSRM.route` computes a fallback route
- **THEN** it SHALL return a mapping providing `"duration"`, `"distance"`, and `"legs"` keys so CLI commands can subscript the result.

#### Scenario: Dataclass responses normalised
- **WHEN** an injected OSRM client returns a dataclass instance
- **THEN** `RoutingAPI.route` SHALL normalise it into the mapping contract before downstream consumers read `result["duration"]`.

#### Scenario: Matrix values preserve list-of-lists access
- **WHEN** `RoutingAPI.matrix` wraps OSRM table responses
- **THEN** the returned structure SHALL include `"durations"` and `"distances"` as list-of-list mappings accessible via dictionary indexing, even if the underlying client emits dataclasses.
