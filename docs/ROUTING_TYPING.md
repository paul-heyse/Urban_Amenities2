# Routing Typing Conventions

The routing stack exposes typed interfaces so `mypy` can validate request and
response handling without relying on implicit `Any` conversions.

## OSRM client
- `OSRMClient.route` returns an `OSRMRoute` dataclass containing the scalar
  duration (seconds), optional distance (metres), and a list of `OSRMLeg`
  entries. Each leg exposes typed duration/distance fields and non-numeric
  payloads from OSRM are rejected during parsing.
- `OSRMClient.table` returns an `OSRMTable` dataclass. Duration and distance
  matrices are represented as `list[list[float | None]]`, preserving
  reachability gaps without widening to `Any`.
- Batched table calls reuse the same dataclasses so downstream code can rely on
  consistent types irrespective of OSRM limits.

## Great-circle fallback
- The CLI fallback (`GreatCircleOSRM`) mirrors the OSRM dataclasses, ensuring
  callers can switch between real and synthetic clients without adjusting type
  expectations.

## Monitoring collectors
- `MetricsCollector.record_timing`, `record_service_call`, and the convenience
  `record` helper all return `None` and persist floats in dedicated dataclasses
  (`_ServiceBucket`). This avoids union-heavy dictionaries while keeping
  summaries fully typed.

## CLI sanitisation
- `_sanitize_properties` accepts any `Mapping[str, object]` and always returns a
  `dict[str, object]` populated with JSON-safe scalars, sequences, or nested
  dictionaries. Tests cover the GeoJSON export path to guarantee sanitised
  properties stay typed.

## Validation
Run the targeted type checks before shipping routing changes:

```bash
mypy src/Urban_Amenities2/router src/Urban_Amenities2/monitoring src/Urban_Amenities2/cli --warn-unused-ignores
```
