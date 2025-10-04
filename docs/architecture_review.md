# Architecture Review and Optimization Opportunities

## Overview
This assessment highlights structural, performance, and reliability opportunities across the AUCS core infrastructure. The goal is to streamline the architecture, reduce long-term maintenance cost, and surface areas where additional hardening will pay off.

## Key Findings

### 1. UI data access layer mixes orchestration, caching, and transformation
`DataContext` currently owns discovery of score files, metadata joining, geometry hydration, aggregation, overlay construction, and export utilities in a single 600+ line module. The class also mutates shared state (`self.geometries`, `_aggregation_cache`, overlays) during read operations, which makes reuse in concurrent contexts risky and complicates targeted testing.【F:src/Urban_Amenities2/ui/data_loader.py†L87-L365】

**Recommendations**
- Split responsibilities into explicit services (e.g., `DatasetCatalog`, `GeometryService`, `OverlayBuilder`) that can be individually composed and unit-tested.
- Convert aggregation and overlay building into pure functions that return data instead of mutating context state, enabling safe concurrency and caching.
- Introduce a lightweight repository abstraction for score/metadata discovery so alternative storage backends (S3, databases) can be added without touching UI logic.

### 2. CLI entrypoint has grown into a monolith
`cli/main.py` instantiates multiple Typer sub-apps and also embeds helper utilities (JSON conversion, great-circle fallback router, weight parsing) inline. The file already mixes routing, scoring, calibration, and ingest command plumbing in one module, making it hard to extend or reuse functionality in other executables and limiting testability.【F:src/Urban_Amenities2/cli/main.py†L1-L195】

**Recommendations**
- Factor each functional area (configuration, ingestion, routing, scoring) into dedicated modules that register commands with the root Typer app, leaving `main.py` focused on bootstrapping.
- Move shared helpers (e.g., `_json_safe`, `_load_table`, `_parse_weights`) into reusable utilities so they can be imported without pulling the entire CLI stack (and its heavy dependencies).
- Introduce command discovery via entry points or module registries to make future capability additions incremental.

### 3. Cache manager lacks pluggable backends and observability hooks
`CacheManager` hardcodes a diskcache backend and exposes Redis as a not-yet-implemented branch. TTL policies live in individual dataclass fields and are reassembled into dictionaries at runtime. There is also no mechanism for surfacing cache statistics beyond an ad-hoc `get_stats` call, and eviction/invalidation logic iterates the entire keyspace for partial invalidations.【F:src/Urban_Amenities2/cache/manager.py†L18-L256】

**Recommendations**
- Define a backend protocol so disk, Redis, or cloud caches can be swapped without modifying the manager; treat TTL policies as a mapping that can be configured externally.
- Emit structured cache events via the shared logging utilities and optionally integrate with Prometheus counters to track hit/miss rates automatically.
- Replace linear key scans in `invalidate` with backend-native prefix operations (e.g., Redis `SCAN`/`DEL` or diskcache tag support) to avoid performance cliffs on large caches.

### 4. Optional GTFS realtime fallback re-implements protobuf semantics
When `google.transit.gtfs_realtime_pb2` is unavailable, the module creates a tree of dataclasses that partially emulate the protobuf API. This dual implementation doubles the surface area to maintain and risks diverging behaviour from the real library over time.【F:io/gtfs/realtime.py†L9-L117】

**Recommendations**
- Extract a thin adapter interface around the protobuf types and load either the real module or a single-purpose fixture implementation for tests.
- Consider serialising fallback feeds into a canonical schema (e.g., pydantic models) and running adapters to/from protobuf to keep business logic independent of the transport library.

### 5. Logging utilities duplicate timing logic and lack central instrumentation
`logging_utils.py` exposes both a contextmanager and decorator that each import `time` locally and emit duration events. The module otherwise provides the sanitisation pipeline, but nothing surfaces metrics or integrates with the caching/routing layers by default.【F:src/Urban_Amenities2/logging_utils.py†L30-L158】

**Recommendations**
- Consolidate timing helpers into a single implementation that can be reused by both the decorator and context manager, reducing drift.
- Add hooks (or contextvar integration) to automatically attach request/run identifiers for CLI and UI operations, enabling end-to-end traceability across threads and processes.
- Evaluate exposing a metrics sink (e.g., StatsD or OpenTelemetry) alongside structlog so latency measurements can inform scaling decisions.

### 6. Test coverage is far below the configured 95 % gate
The latest coverage artefact shows only 2 216 of 6 641 executable lines covered (≈33 %), implying large swathes of the pipeline—particularly UI and caching layers—lack regression protection.【F:coverage.xml†L2-L3】

**Recommendations**
- Prioritise high-value integration tests around the UI data services and routing/cache boundaries once those modules are decomposed.
- Add contract tests for CLI commands that mock expensive dependencies to keep the coverage gate meaningful without inflating runtime.
- Track per-package coverage so future contributions can focus on the most critical gaps.

## Next Steps
1. Align stakeholders on the proposed module boundaries for UI data loading and CLI command registration.
2. Pilot the cache backend abstraction with a Redis implementation and add structured metrics for hit/miss tracking.
3. Establish a coverage improvement plan (or adjust the gate temporarily) while the refactors above increase testability.
