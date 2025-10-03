# Type Safety Error Catalog — 2025-10-03

Generated from `mypy src/Urban_Amenities2 --warn-unused-ignores`.

Total outstanding errors: **104** across **37** modules. Grouped by subsystem below.

## UI Layer
Modules: `ui/performance.py`, `ui/hex_selection.py`, `ui/export.py`, `ui/logging.py`, `ui/layers.py`, `ui/callbacks.py`, `ui/layouts/*`.
- Dictionary comprehensions mixing `dict[str, float]` with `None` (performance).
- State containers overwritten with `None` (hex selection).
- GeoJSON export fields mutated from `str` to numeric types (export).
- Logger helper returning structlog logger rather than stdlib type (logging).
- Plotly trace type alias unresolved (`go.BaseTraceType`) plus layer typing (layers, callbacks).
- Dash dropdown options built from raw dicts instead of typed sequences (layouts).
Total errors: **18**.

## Routing & Monitoring
Modules: `router/osrm.py`, `monitoring/metrics.py`, `monitoring/health.py`, `ui/performance.py`, `cli/main.py`, `scores/mobility_reliability.py`.
- OSRM client request parameters typed as invariant `dict`, response helpers returning `Any`.
- Metrics accumulators storing `list[float] | int`, violating typing assumptions.
- Optional psutil module assignment flagged.
- CLI exports sanitising property dictionaries incorrectly typed.
- Mobility reliability score using unions for Series computations.
Total errors: **21**.

## Scoring & Math
Modules: `scores/corridor_trip_chaining.py`, `scores/corridor_enrichment.py`, `scores/seasonal_outdoors.py`, `scores/leisure_culture_access.py`, `scores/hub_airport_access.py`, `scores/essentials_access.py`, `math/ces.py`, `quality/dedupe.py`, `dedupe/pois.py`, `quality/scoring.py`.
- Corridor/seasonal modules rely on shapely geometries and pandas operations returning `Any`.
- Leisure & essentials configs treat Series values as arbitrary hashables.
- Hub/airport score dataclasses declare `__slots__` conflicting with class vars.
- Math helpers (`ces`, `quality/dedupe`, `dedupe/pois`) return untyped ndarrays.
- Quality scoring selectors operate on unions and return `Any` Series.
Total errors: **32**.

## Data Ingestion
Modules: `io/overture/places.py`, `io/overture/transportation.py`, `io/parks/ridb.py`, `io/enrichment/wikipedia.py`, `io/gtfs/realtime.py`.
- Optional dependency fallbacks (`google.cloud.bigquery`, shapely) assigned `None`.
- HTTP params typed as `dict[str, object]`, incompatible with `requests` expectations.
- GeoDataFrame helpers returning `DataFrame | Series` unions.
- GTFS realtime fallback serializer returning `Any` bytes.
Total errors: **18**.

## Accessibility & Matrices
Modules: `accessibility/matrices.py`, `scores/corridor_trip_chaining.py` (shared data concerns).
- Dictionary lookups keyed by unions from pandas indexes.
Total errors: **3**.

## Configuration
Module: `config/params.py`.
- Pydantic validator signature mismatch, field redeclaration, optional float assignment, default factory typing.
Total errors: **4**.

## Summary
| Category | Error Count |
| --- | --- |
| UI Layer | 18 |
| Routing & Monitoring | 21 |
| Scoring & Math | 32 |
| Data Ingestion | 18 |
| Accessibility & Matrices | 3 |
| Configuration | 4 |
| **Total** | **104** |

Use this catalog with the accompanying change proposals to schedule remediation work.
