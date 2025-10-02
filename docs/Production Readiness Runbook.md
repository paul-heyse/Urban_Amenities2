# Production Readiness Runbook

This runbook captures the operational procedures and instrumentation introduced for the `add-production-readiness` scope.

## 1. Routing service deployment

### OSRM (car, bike, foot)
1. Export Overture Transportation tiles for CO/UT/ID (`overture_transportation.parquet`) using the data acquisition scripts.
2. Convert to `.osm.pbf` with [`osmium`](https://osmcode.org/osmium-tool/):
   ```bash
   osmium tags-filter overture_transportation.pbf w/highway -o transport.osm.pbf
   ```
3. Build graphs per profile:
   ```bash
   osrm-extract -p profiles/car.lua transport.osm.pbf
   osrm-contract transport.osrm
   # Repeat for bike.lua and foot.lua
   ```
4. Containerise services with the supplied Docker Compose (`docker/osrm-compose.yml`) pointing to environment variables `OSRM_CAR_URL`, `OSRM_BIKE_URL`, and `OSRM_FOOT_URL`.
5. Register the graph build in `runs/manifests.jsonl` (`graph_version`, `built_at`, `overture_snapshot`).
6. Schedule quarterly rebuilds by re-running steps 1–5 and archiving the previous `.osrm` files under `data/archive/osrm/<date>`.

### OpenTripPlanner 2
1. Download GTFS feeds for all agencies in CO/UT/ID using `python -m Urban_Amenities2.io.gtfs.registry` (Transitland registry).
2. Validate feeds with `gtfs-kit doctor` and store HTML reports in `data/qa/gtfs`.
3. Export the Overture street network (`prepare_transportation --otp`) to `otp_streets.osm.pbf`.
4. Build the OTP graph:
   ```bash
   java -Xmx12G -jar otp-shaded.jar --build --save graphs/mountain_west
   ```
5. Run OTP2 via Docker with `OTP_URL` and enable the health endpoint.
6. Record feed hashes and graph version in the manifest and schedule weekly rebuilds.

## 2. External API hardening

* Store API keys in the configured secrets backend (`.env` for dev, Vault/AWS Secrets Manager for prod).
* All outbound API calls use `tenacity` with exponential backoff and jitter (configured globally in `logging_utils`); failures raise alerts via structured logs.
* Caching defaults: Wikipedia 24h, Wikidata 7d, stored in `data/cache` (size cap 10GB enforced by disk quota checks).

## 3. Monitoring & metrics

* `Urban_Amenities2.monitoring.metrics.METRICS` collects:
  * Timing metrics for stage joins (`sou_join`, `parks_accessibility`).
  * Throughput metrics for parks aggregation (`parks_hexes`).
  * Service latency/success rates for `osrm_{car,bike,foot}` and `otp` health probes.
* Use `python -m Urban_Amenities2.monitoring.metrics` to dump `METRICS.serialise()` for Prometheus scraping.
* All operations log JSON events with `operation_start` / `operation_complete`, including `duration_seconds`, `items`, and stage-specific metadata.

## 4. Health checks & graceful degradation

* `aucs healthcheck` now records metric samples and fails fast when routing services or OTP are unreachable.
* When a dependency is down, ingestion modules emit warning logs and skip optional enrichments rather than halting the pipeline.
* Disk and memory checks guard against insufficient resources (thresholds: 100GB free disk, 8GB RAM).

## 5. QA visualisation

* Generate SOU QA GeoJSON with `aucs export` after running `SeasonalOutdoorsCalculator.from_parks_data`; the CLI normalises numpy/pandas types for GeoJSON compatibility.
* Load the exported GeoJSON in the dashboard to inspect climate-adjusted choropleths.

## 6. Documentation & logging schema

* Logs include: `timestamp`, `level`, `logger`, `message`, `request_id`, `operation`, `duration_seconds`, and stage-specific fields.
* Sanitisation masks secrets, rounds coordinates, and hashes identifiers; `tests/test_logging.py` parses JSON logs to ensure structure.

Keep this runbook updated as infrastructure evolves. For incident response, capture `METRICS.serialise()` output and the latest health check results to diagnose service regressions.
