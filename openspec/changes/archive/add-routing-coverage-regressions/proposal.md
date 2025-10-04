## Why
Routing modules (OSRM/OTP clients, routing API, CLI commands) are still poorly covered and currently break when stub behaviour changes. Increasing coverage here is essential to reach the new 85% routing minimum and to prevent regressions like the OSRM dataclass issue.

## What Changes
- Expand unit tests for `RoutingAPI`, `OSRMClient`, `GreatCircleOSRM`, and CLI commands to cover success, error, and edge cases.
- Add fixtures and factories that simulate OSRM/OTP responses with dataclass and dict payloads.
- Ensure routing tests run without network access and validate coverage metrics.

## Impact
- Affected specs: testing
- Affected code: `tests/test_routing.py`, `tests/test_cli.py`, routing fixtures under `tests/conftest.py`, routing clients in `src/Urban_Amenities2/router`
