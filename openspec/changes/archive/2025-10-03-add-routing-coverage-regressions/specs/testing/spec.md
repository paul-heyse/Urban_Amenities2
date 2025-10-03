## ADDED Requirements

### Requirement: Routing Regression Coverage
Routing clients, APIs, and CLI commands SHALL be covered by deterministic tests to sustain the 85% routing coverage target.

#### Scenario: OSRM client coverage
- **WHEN** running `pytest tests/test_routing.py -k osrm`
- **THEN** tests SHALL assert route batching, table concatenation, and error handling for OSRM responses (including dict and dataclass payloads)
- **AND** no external HTTP requests SHALL be made

#### Scenario: RoutingAPI matrix coverage
- **WHEN** running `pytest tests/test_routing.py -k matrix`
- **THEN** `RoutingAPI.matrix` SHALL be exercised for car and transit modes, covering duration-only tables, missing distances, and cache hits

#### Scenario: CLI routing coverage
- **WHEN** running `pytest tests/test_cli.py -k routing`
- **THEN** the `routing compute-skims` command SHALL be tested end-to-end with temporary CSV inputs and exported Parquet outputs, ensuring coverage reflects the CLI workflow
