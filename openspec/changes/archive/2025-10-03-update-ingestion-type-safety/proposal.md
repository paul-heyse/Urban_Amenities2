## Why
Data ingestion modules (Overture BigQuery readers, RIDB parks importer, Wikipedia enrichment, GTFS realtime fallbacks) still emit 18 mypy errors caused by optional dependency handling, shapely geometry returns, and request parameter typing. These modules interface with external services; untyped code raises integration risk and impedes full type-safety adoption.

## What Changes
- Clarify optional dependency patterns for BigQuery and shapely usage, ensuring fallbacks expose typed interfaces and avoid module-level `None` assignments.
- Annotate file/HTTP ingestion utilities (`io/overture/places.py`, `io/overture/transportation.py`, `io/parks/ridb.py`, `io/enrichment/wikipedia.py`) with typed DataFrame outputs and typed request payloads.
- Harden GTFS realtime fallbacks to return typed bytes/records and ensure structured message parsing.
- Update ingestion tests/fixtures to validate typed outputs and optional dependency scenarios.

## Impact
- Affected specs: `qa/ingestion-type-safety`
- Affected code: `io/overture/*`, `io/parks/ridb.py`, `io/enrichment/wikipedia.py`, `io/gtfs/realtime.py`, plus related tests and docs.
