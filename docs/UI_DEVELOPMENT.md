# Urban Amenities UI Development Guide

This document describes how to run and iterate on the Dash-based Urban Amenities Explorer.

## Prerequisites

- Python environment with the project dependencies installed (`pip install -r requirements-ui.txt`).
- Access to AUCS model outputs in Parquet format (place files under `data/outputs`).
- Optional: Mapbox API token for enhanced basemap styles (`export MAPBOX_TOKEN=...`).

## Running Locally

```bash
# Activate the project environment
micromamba activate ./

# Install UI dependencies
pip install -r requirements-ui.txt

# Start the UI with hot reload
python -m Urban_Amenities2.ui.run
```

The application listens on `http://localhost:8050` by default. Hot reload is enabled through Dash when `UI_DEBUG=true`.

## Environment Variables

| Variable | Description | Default |
| -------- | ----------- | ------- |
| `UI_HOST` | Interface to bind the Dash server | `0.0.0.0` |
| `UI_PORT` | Port number for the UI | `8050` |
| `UI_DEBUG` | Enables Dash debug mode with hot reload | `false` |
| `UI_DATA_PATH` | Directory containing AUCS Parquet outputs | `data/outputs` |
| `UI_RELOAD_INTERVAL` | Seconds between automatic dataset refresh checks | `30` |
| `UI_CORS_ORIGINS` | Comma-separated list of allowed origins | `*` |
| `MAPBOX_TOKEN` | Mapbox access token | none |

## Data Workflow

1. Place AUCS Parquet files (`*.parquet`) and optional `metadata.parquet` under `data/outputs`.
2. The UI automatically loads the latest file based on modification time and caches hexagon geometries.
3. Use the **Data** page to refresh, export CSV/GeoJSON, and inspect the active dataset version.
4. The **Map Explorer** provides filters by state, metro, county, and score ranges; adjust subscore weights in the advanced panel to preview composite scenarios.

## Docker & Reverse Proxy

A ready-to-run Docker Compose configuration is available in `docker-compose.ui.yml` with a complementary Nginx reverse proxy under `configs/nginx/ui.conf`.

```bash
docker compose -f docker-compose.ui.yml up --build
```

This starts both the UI and proxy services. Health checks target `/health` and static assets are cached for an hour.

## Development Seed Data

Use the helper script `scripts/generate_ui_sample_data.py` to generate a synthetic dataset with 1,000 hexes suitable for UI prototyping.

```bash
python scripts/generate_ui_sample_data.py --output data/outputs
```

The script fabricates AUCS subscores, metadata (state/metro/county), and ensures geometries are resolvable via H3. This enables rapid UI iteration without full pipeline outputs.

## Logging

Logging is configured through the `UI_LOG_LEVEL` environment variable (INFO by default). Logs are emitted via the shared project logging utilities to keep structured JSON output when running behind Gunicorn.

## Troubleshooting

- **Missing H3 geometries** – ensure the `h3` Python package is installed and the hex IDs are valid at resolutions 6-9.
- **Empty maps** – confirm the Parquet files include `hex_id` and `aucs` columns; use the Data page refresh button after updating data files.
- **Mapbox token errors** – provide a valid token via `MAPBOX_TOKEN` or switch to open styles like `carto-positron`.

Happy mapping!
