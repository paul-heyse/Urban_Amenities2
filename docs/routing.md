# Routing Engines

The AUCS routing stack combines OSRM for street-based modes and OTP2 for transit
planning. This document outlines how to prepare data, configure engines, and run
matrix computations using the Typer CLI.

## OSRM

1. **Build extracts** – Use `io.overture.transportation.export_networks` to
   generate GeoJSON per mode from the Overture transportation segments. Example:
   ```bash
   aucs routing build-osrm data/processed/transport_segments.parquet --profile car --output-dir data/osrm
   ```
   This writes `network_car.geojson`, `network_bike.geojson`, and
   `network_foot.geojson` for OSRM preprocessing.
2. **Serve OSRM** – Follow the standard OSRM pipeline (`osrm-extract`,
   `osrm-partition`, `osrm-customize`, `osrm-routed`). Point the AUCS CLI at the
   running server via `--osrm-base-url` when computing skims.
3. **Fallback** – When an OSRM endpoint is unavailable the CLI falls back to the
   built-in `GreatCircleOSRM` implementation which uses haversine distances and
   mode-specific default speeds.

## OTP2

1. **Assemble inputs** – Place GTFS zip files (produced by `io.gtfs.static`) in a
   directory alongside the exported street network.
2. **Build graph** – Use the helper command to create a manifest:
   ```bash
   aucs routing build-otp data/processed/gtfs --output-path data/otp/manifest.json
   ```
   The manifest lists feeds and timestamps, simplifying automation around OTP
   graph builds.
3. **Queries** – `router.otp.OTPClient` implements the Transmodel GraphQL
   endpoint, returning itineraries with walk/transit/wait components, transfers,
   and fare information.

## Matrix Computation

`router.batch.SkimBuilder` wraps `RoutingAPI` to cache many-to-many travel time
matrices using `diskcache`. The CLI command ties everything together:

```bash
aucs routing compute-skims origins.csv destinations.csv --mode car --period AM --output-path data/processed/skims_car_AM.parquet
```

* Origins/Destinations – CSV or Parquet files with columns `id`, `lat`, `lon`.
* Modes – `car`, `bike`, `foot` use OSRM; `transit` routes through OTP.
* Output – Parquet table with duration/distance for each OD pair plus indices
  that map back to the input IDs.

For examples, inspect `tests/test_routing.py` and the CLI tests in
`tests/test_cli.py`.
