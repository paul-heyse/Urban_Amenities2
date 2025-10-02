# AUCS Core Infrastructure

This repository contains the foundational infrastructure for the Aker Urban
Convenience Score (AUCS) model. It provides:

- Typed parameter management with Pydantic models and YAML loaders
- H3-based spatial utilities for points, lines, and polygons
- Pandera schemas covering spatial, travel, and scoring datasets
- Reproducibility tracking via run manifests and data snapshots
- Structlog-based logging helpers and a Typer CLI for configuration/run tasks

## Getting Started

1. Install dependencies in your environment (see `pyproject.toml`).
2. Review the example configuration at `configs/params_default.yml`.
3. Validate the configuration:
   ```bash
   python -m Urban_Amenities2.cli.main config-validate configs/params_default.yml
   ```
4. Inspect a location's hexagon:
   ```bash
   python -m Urban_Amenities2.cli.main hex-info 39.7392 -104.9903
   ```
5. Initialise a run manifest:
   ```bash
   python -m Urban_Amenities2.cli.main run-init configs/params_default.yml --git-commit $(git rev-parse HEAD)
   ```

See `docs/architecture.md` and `docs/configuration.md` for detailed component
and parameter overviews.
