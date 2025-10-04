## 1. Implementation
- [x] 1.1 Reintroduce a mapping-compatible return structure for OSRM route/table helpers while keeping typed access (e.g., via dataclass `.as_dict()` or lightweight adapters).
- [x] 1.2 Update `RoutingAPI.route`/`matrix` to normalise heterogeneous client responses (dicts vs dataclasses) and cover transit fallbacks.
- [x] 1.3 Extend routing unit tests (`tests/test_routing.py`) to assert dict-style access and attribute access both succeed for OSRM clients and the CLI stub.
- [x] 1.4 Run `pytest -q` for routing-focused suites and ensure coverage thresholds remain ≥95%.
