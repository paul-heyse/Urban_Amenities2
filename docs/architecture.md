# AUCS Core Infrastructure Architecture

The AUCS 2.0 core infrastructure layers the foundational services that future
model components rely on. The package is organised by responsibility:

- `Urban_Amenities2/config/`: typed configuration models powered by Pydantic
  along with YAML loading helpers and deterministic hashing utilities.
- `Urban_Amenities2/hex/`: reusable H3 helpers for coordinate conversion,
  geometry lookup, and spatial aggregation (points, lines, polygons).
- `Urban_Amenities2/schemas/`: Pandera DataFrame schemas that enforce column
  presence and value ranges for spatial, travel, and scoring datasets.
- `Urban_Amenities2/versioning/`: lightweight reproducibility primitives for
  managing data snapshots and run manifests backed by JSONL storage.
- `Urban_Amenities2/logging_utils.py`: structlog configuration and timing
  helpers for consistent structured logging across the pipeline.
- `Urban_Amenities2/cli/`: Typer-driven CLI that validates configurations,
  inspects hexagons, and manages run manifests.

Supporting assets include an example parameter configuration under
`configs/params_default.yml` plus integration tests under `tests/` that cover
end-to-end parameter loading, schema validation, spatial utilities, and the CLI.
