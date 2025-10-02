# AUCS Core Infrastructure

This repository contains the foundational infrastructure for the Aker Urban
Convenience Score (AUCS) model. It now bundles data ingestion, routing,
accessibility, scoring, aggregation, and export tooling.

## Capabilities

- Typed parameter management with Pydantic models and YAML loaders
- H3-based spatial utilities for points, lines, and polygons
- Routing integrations for OSRM (auto/bike/foot) and OTP2 (transit)
- Travel-time matrices and accessibility builders feeding Essentials Access
- Pandera schemas for spatial, travel, and scoring datasets
- Reproducibility tracking via run manifests and data snapshots
- Structlog-based logging helpers and a Typer CLI for configuration, ingestion,
  routing, scoring, and export tasks

## Getting Started

1. Install dependencies in your environment (see `pyproject.toml`).
2. Review the example configuration at `configs/params_default.yml`.
3. Validate the configuration:
   ```bash
   python -m Urban_Amenities2.cli.main config validate configs/params_default.yml
   ```
4. Inspect a location's hexagon:
   ```bash
   python -m Urban_Amenities2.cli.main hex info 39.7392 -104.9903
   ```
5. Initialise a run manifest:
   ```bash
   python -m Urban_Amenities2.cli.main run init configs/params_default.yml --git-commit $(git rev-parse HEAD)
   ```

### Data Ingestion

Use the CLI to ingest Overture, GTFS, and supporting datasets once raw files are
available locally or via cloud storage:

```bash
python -m Urban_Amenities2.cli.main ingest overture-places data/raw/overture_places_co.parquet
python -m Urban_Amenities2.cli.main ingest gtfs "Regional Transportation District"
python -m Urban_Amenities2.cli.main data quality-report --pois-path data/processed/pois.parquet
```

See `docs/data_sources.md`, `docs/data_pipeline.md`, and the example script in
`examples/ingest_co_data.py` for end-to-end orchestration guidance.

### Routing and Accessibility

Prepare OSRM/OTP assets and compute skims:

```bash
python -m Urban_Amenities2.cli.main routing build-osrm data/processed/transport_segments.parquet
python -m Urban_Amenities2.cli.main routing compute-skims origins.csv destinations.csv --mode car --period AM
```

Refer to `docs/routing.md` for deployment details.

### Essentials Access Scoring

Generate Essentials Access scores once POIs and accessibility matrices are
ready:

```bash
python -m Urban_Amenities2.cli.main score ea data/processed/pois.parquet data/processed/accessibility.parquet
python -m Urban_Amenities2.cli.main calibrate ea data/processed/pois.parquet data/processed/accessibility.parquet --parameter rho:groceries --values 0.4,0.6,0.8
```

Documentation lives in `docs/subscores/essentials_access.md` and the quickstart
notebook `examples/compute_ea.ipynb`.

### Aggregation and Export

The CLI exposes aggregation and export helpers (see `python -m
Urban_Amenities2.cli.main --help`). `export/parquet.py` and `export/reports.py`
provide programmatic access to score files, explainability tables, and QA
reports.

## Further Reading

- `docs/architecture.md` – high-level system overview
- `docs/configuration.md` – parameter catalogue and schema docs
- `docs/categories.md` – AUCS category crosswalk guidance
- `docs/data_sources.md` / `docs/data_pipeline.md` – ingestion specifics
- `docs/routing.md` – routing engine setup
- `docs/subscores/essentials_access.md` – Essentials Access methodology
