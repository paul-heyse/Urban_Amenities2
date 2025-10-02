## 1. Project Setup & Dependencies

- [x] 1.1 Create `pyproject.toml` with core dependencies (h3, pydantic>=2.0, ruamel.yaml, pandera, structlog, typer, numpy, pandas)
- [x] 1.2 Set up `src/Urban_Amenities2/` package structure
- [x] 1.3 Configure pytest, ruff, black in pyproject.toml
- [x] 1.4 Create initial `README.md` with project overview

## 2. Parameter Management (Pydantic Models)

- [x] 2.1 Create `src/Urban_Amenities2/config/params.py` with models for:
  - [x] 2.1.1 GridConfig (hex_size_m, isochrone_minutes, search_cap_minutes)
  - [x] 2.1.2 SubscoreWeights (EA, LCA, MUHAA, JEA, MORR, CTE, SOU summing to 100)
  - [x] 2.1.3 TimeSliceConfig (id, weight, VOT_per_hour)
  - [x] 2.1.4 ModeConfig (theta_iv, theta_wait, theta_walk, transfer_penalty_min, half_life_min, beta0, reliability_buffer, etc.)
  - [x] 2.1.5 NestConfig (modes list, mu, eta)
  - [x] 2.1.6 LogitConfig (mu_top)
  - [x] 2.1.7 CarryPenaltyConfig (category_multipliers, per_mode_extra_minutes)
  - [x] 2.1.8 QualityConfig (lambda weights, z_clip_abs, opening_hours_bonus_xi, dedupe_beta_per_km)
  - [x] 2.1.9 CategoryConfig (essentials list, leisure list, ces_rho, satiation_kappa, diversity)
  - [x] 2.1.10 LeisureCrossCategoryConfig (weights, elasticity_zeta, novelty)
  - [x] 2.1.11 HubsAirportsConfig (hub_mass_lambda, decay, airport weights)
  - [x] 2.1.12 JobsEducationConfig (university_weight_kappa, industry_weights)
  - [x] 2.1.13 MORRConfig (frequent_exposure, span, reliability, redundancy, micromobility)
  - [x] 2.1.14 CorridorConfig (max_paths, stop_buffer_m, detour_cap_min, pair_categories, walk_decay_alpha)
  - [x] 2.1.15 SeasonalityConfig (comfort defaults)
  - [x] 2.1.16 NormalizationConfig (mode, metro_percentile, standards)
  - [x] 2.1.17 ComputeConfig (topK_per_category, hub_max_minutes, etc.)
- [x] 2.2 Create root `AUCSParams` model composing all sub-configs
- [x] 2.3 Implement YAML loader with validation in `src/Urban_Amenities2/config/loader.py`
- [x] 2.4 Add parameter versioning (hash computation from canonical YAML)
- [x] 2.5 Write tests for parameter loading and validation

## 3. H3 Spatial Grid Operations

- [x] 3.1 Create `src/Urban_Amenities2/hex/core.py` with:
  - [x] 3.1.1 Function to convert lat/lon to H3 cell at resolution 9
  - [x] 3.1.2 Function to get hex centroid
  - [x] 3.1.3 Function to get hex boundary polygon
  - [x] 3.1.4 Function to compute hex-to-hex distance
  - [x] 3.1.5 Function to get k-ring neighbors
- [x] 3.2 Create `src/Urban_Amenities2/hex/aggregation.py` with:
  - [x] 3.2.1 Spatial join: points to hexes
  - [x] 3.2.2 Spatial join: lines to hexes (for segments)
  - [x] 3.2.3 Spatial join: polygons to hexes (area-weighted)
  - [x] 3.2.4 Hex-level aggregation utilities
- [x] 3.3 Add performance optimizations (vectorized operations, caching)
- [x] 3.4 Write comprehensive tests for H3 operations

## 4. Data Schemas & Validation

- [x] 4.1 Create `src/Urban_Amenities2/schemas/spatial.py` with Pandera schemas for:
  - [x] 4.1.1 HexIndex (hex_id, centroid_lat, centroid_lon, geometry)
  - [x] 4.1.2 POI (poi_id, hex_id, aucstype, name, brand, lat, lon, quality_attrs)
  - [x] 4.1.3 NetworkSegment (segment_id, hex_id, geometry, mode_flags, speed)
- [x] 4.2 Create `src/Urban_Amenities2/schemas/travel.py` with schemas for:
  - [x] 4.2.1 TravelTimeSkim (origin_hex, dest_hex, mode, period, duration_min, distance_m, ok)
  - [x] 4.2.2 TransitItinerary (origin_hex, dest_hex, period, walk_time, transit_time, wait_time, transfers, fare_usd)
- [x] 4.3 Create `src/Urban_Amenities2/schemas/scores.py` with schemas for:
  - [x] 4.3.1 CategoryScore (hex_id, category, raw_score, normalized_score)
  - [x] 4.3.2 Subscore (hex_id, subscore_name, value, contributors)
  - [x] 4.3.3 FinalScore (hex_id, aucs, subscores_dict, metadata)
- [x] 4.4 Add validation decorators for all data pipeline steps
- [x] 4.5 Write tests for schema validation

## 5. Versioning & Reproducibility

- [x] 5.1 Create `src/Urban_Amenities2/versioning/manifest.py` with:
  - [x] 5.1.1 RunManifest model (run_id, timestamp, param_hash, data_snapshot_ids, git_commit)
  - [x] 5.1.2 Function to create run manifest
  - [x] 5.1.3 Function to serialize/deserialize manifests
- [x] 5.2 Create `src/Urban_Amenities2/versioning/data_snapshot.py` with:
  - [x] 5.2.1 DataSnapshot model (source_name, version, download_date, file_hash)
  - [x] 5.2.2 Snapshot registration utilities
- [x] 5.3 Implement run tracking storage (local JSONL or SQLite)
- [x] 5.4 Add CLI commands for run management (`aucs run list`, `aucs run show`)
- [x] 5.5 Write tests for versioning system

## 6. Logging & Error Handling

- [x] 6.1 Configure structlog with JSON formatter for production
- [x] 6.2 Create custom logger with context (run_id, stage, hex_id)
- [x] 6.3 Define standard log levels and messages
- [x] 6.4 Add performance logging utilities (timing decorators)
- [x] 6.5 Create error classification system (data errors, computation errors, validation errors)

## 7. CLI Foundation

- [x] 7.1 Create `src/Urban_Amenities2/cli/main.py` with Typer app
- [x] 7.2 Add `aucs config validate <yaml>` command
- [x] 7.3 Add `aucs config show` command to display loaded params
- [x] 7.4 Add `aucs hex info <lat> <lon>` command for spatial debugging
- [x] 7.5 Add `aucs run init` command to start new scoring run
- [x] 7.6 Write tests for CLI commands

## 8. Integration & Documentation

- [x] 8.1 Write `docs/architecture.md` explaining core systems
- [x] 8.2 Write `docs/configuration.md` documenting all parameters
- [x] 8.3 Create example parameter YAML in `configs/params_default.yml`
- [x] 8.4 Add docstrings to all public functions
- [x] 8.5 Create integration tests for the full parameter→schema pipeline
- [x] 8.6 Update main README with setup instructions
