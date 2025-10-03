## Why
Routing, monitoring, and CLI utilities contribute 21 of the remaining mypy failures, primarily from loosely typed OSRM client requests, metrics collectors that coerce unions at runtime, and CLI export helpers mutating data structures. These errors block end-to-end type safety and mask potential runtime faults (e.g., malformed OSRM parameters, incorrect GeoJSON properties).

## What Changes
- Rework `router/osrm.py` client interfaces to accept typed mappings, return structured tables, and eliminate `Any` shims.
- Tighten monitoring utilities (`monitoring/metrics.py`, `monitoring/health.py`) to use well-defined accumulator data structures and optional dependencies.
- Update CLI and UI performance helpers to ensure sanitized exports and routing fallbacks maintain typed contracts.
- Add focused tests (unit or integration) that validate typed interfaces for OSRM batching, metrics aggregation, and CLI exports.

## Impact
- Affected specs: `qa/routing-type-safety`
- Affected code: `router/osrm.py`, `monitoring/metrics.py`, `monitoring/health.py`, `cli/main.py`, supporting utilities and tests.
