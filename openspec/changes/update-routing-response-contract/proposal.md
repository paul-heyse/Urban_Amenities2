## Why
Recent routing refactors replaced dict-based OSRM payloads with dataclasses, but the public `RoutingAPI` and CLI still expect mapping semantics. Tests now fail with `TypeError: 'OSRMRoute' object is not subscriptable` and `AttributeError: 'dict' object has no attribute 'duration'`, blocking routing regression coverage.

## What Changes
- Restore a stable mapping contract for OSRM client results while preserving typed accessors.
- Update `RoutingAPI` helpers to accept either dicts or dataclass responses without breaking existing call sites.
- Add regression tests around `GreatCircleOSRM` and `RoutingAPI.matrix` to lock the expected contract.

## Impact
- Affected specs: routing
- Affected code: `src/Urban_Amenities2/router/osrm.py`, `src/Urban_Amenities2/router/api.py`, CLI routing helpers and tests
