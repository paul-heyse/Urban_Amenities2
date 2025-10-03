## 1. Client Coverage
- [x] 1.1 Add tests covering OSRM client happy path, batching, error codes, and distance-less responses.
- [x] 1.2 Exercise OTP client planners with success and failure scenarios, ensuring GraphQL payload parsing is validated.

## 2. RoutingAPI & CLI Tests
- [x] 2.1 Extend `tests/test_routing.py` to validate matrix batching, transit fallbacks, and dataclass/dict interop.
- [x] 2.2 Add CLI tests for `routing compute-skims` and `score ea` that assert coverage over file export paths and failure handling.

## 3. Infrastructure
- [x] 3.1 Harden routing fixtures (`StubSession`, OTP/OSRM stubs) to support coverage instrumentation without network calls.
- [x] 3.2 Update coverage reporting to verify `src/Urban_Amenities2/router` meets the 85% target.
