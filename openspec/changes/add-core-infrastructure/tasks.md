## 1. Project Setup & Dependencies

- [ ] 1.1 Create `pyproject.toml` with core dependencies (h3, pydantic>=2.0, ruamel.yaml, pandera, structlog, typer, numpy, pandas)
- [ ] 1.2 Set up `src/Urban_Amenities2/` package structure
- [ ] 1.3 Configure pytest, ruff, black in pyproject.toml
- [ ] 1.4 Create initial `README.md` with project overview

## 2. Parameter Management (Pydantic Models)

- [ ] 2.1 Create `src/Urban_Amenities2/config/params.py` with models for:
  - [ ] 2.1.1 GridConfig (hex_size_m, isochrone_minutes, search_cap_minutes)
  - [ ] 2.1.2 SubscoreWeights (EA, LCA, MUHAA, JEA, MORR, CTE, SOU summing to 100)
  - [ ] 2.1.3 TimeSliceConfig (id, weight, VOT_per_hour)
  - [ ] 2.1.4 ModeConfig (theta_iv, theta_wait, theta_walk, transfer_penalty_min, half_life_min, beta0, reliability_buffer, etc.)
  - [ ] 2.1.5 NestConfig (modes list, mu, eta)
  - [ ] 2.1.6 LogitConfig (mu_top)
  - [ ] 2.1.7 CarryPenaltyConfig (category_multipliers, per_mode_extra_minutes)
  - [ ] 2.1.8 QualityConfig (lambda weights, z_clip_abs, opening_hours_bonus_xi, dedupe_beta_per_km)
  - [ ] 2.1.9 CategoryConfig (essentials list, leisure list, ces_rho, satiation_kappa, diversity)
  - [ ] 2.1.10 LeisureCrossCategoryConfig (weights, elasticity_zeta, novelty)
  - [ ] 2.1.11 HubsAirportsConfig (hub_mass_lambda, decay, airport weights)
  - [ ] 2.1.12 JobsEducationConfig (university_weight_kappa, industry_weights)
  - [ ] 2.1.13 MORRConfig (frequent_exposure, span, reliability, redundancy, micromobility)
  - [ ] 2.1.14 CorridorConfig (max_paths, stop_buffer_m, detour_cap_min, pair_categories, walk_decay_alpha)
  - [ ] 2.1.15 SeasonalityConfig (comfort defaults)
  - [ ] 2.1.16 NormalizationConfig (mode, metro_percentile, standards)
  - [ ] 2.1.17 ComputeConfig (topK_per_category, hub_max_minutes, etc.)
- [ ] 2.2 Create root `AUCSParams` model composing all sub-configs
- [ ] 2.3 Implement YAML loader with validation in `src/Urban_Amenities2/config/loader.py`
- [ ] 2.4 Add parameter versioning (hash computation from canonical YAML)
- [ ] 2.5 Write tests for parameter loading and validation

## 3. H3 Spatial Grid Operations

- [ ] 3.1 Create `src/Urban_Amenities2/hex/core.py` with:
  - [ ] 3.1.1 Function to convert lat/lon to H3 cell at resolution 9
  - [ ] 3.1.2 Function to get hex centroid
  - [ ] 3.1.3 Function to get hex boundary polygon
  - [ ] 3.1.4 Function to compute hex-to-hex distance
  - [ ] 3.1.5 Function to get k-ring neighbors
- [ ] 3.2 Create `src/Urban_Amenities2/hex/aggregation.py` with:
  - [ ] 3.2.1 Spatial join: points to hexes
  - [ ] 3.2.2 Spatial join: lines to hexes (for segments)
  - [ ] 3.2.3 Spatial join: polygons to hexes (area-weighted)
  - [ ] 3.2.4 Hex-level aggregation utilities
- [ ] 3.3 Add performance optimizations (vectorized operations, caching)
- [ ] 3.4 Write comprehensive tests for H3 operations

## 4. Data Schemas & Validation

- [ ] 4.1 Create `src/Urban_Amenities2/schemas/spatial.py` with Pandera schemas for:
  - [ ] 4.1.1 HexIndex (hex_id, centroid_lat, centroid_lon, geometry)
  - [ ] 4.1.2 POI (poi_id, hex_id, aucstype, name, brand, lat, lon, quality_attrs)
  - [ ] 4.1.3 NetworkSegment (segment_id, hex_id, geometry, mode_flags, speed)
- [ ] 4.2 Create `src/Urban_Amenities2/schemas/travel.py` with schemas for:
  - [ ] 4.2.1 TravelTimeSkim (origin_hex, dest_hex, mode, period, duration_min, distance_m, ok)
  - [ ] 4.2.2 TransitItinerary (origin_hex, dest_hex, period, walk_time, transit_time, wait_time, transfers, fare_usd)
- [ ] 4.3 Create `src/Urban_Amenities2/schemas/scores.py` with schemas for:
  - [ ] 4.3.1 CategoryScore (hex_id, category, raw_score, normalized_score)
  - [ ] 4.3.2 Subscore (hex_id, subscore_name, value, contributors)
  - [ ] 4.3.3 FinalScore (hex_id, aucs, subscores_dict, metadata)
- [ ] 4.4 Add validation decorators for all data pipeline steps
- [ ] 4.5 Write tests for schema validation

## 5. Versioning & Reproducibility

- [ ] 5.1 Create `src/Urban_Amenities2/versioning/manifest.py` with:
  - [ ] 5.1.1 RunManifest model (run_id, timestamp, param_hash, data_snapshot_ids, git_commit)
  - [ ] 5.1.2 Function to create run manifest
  - [ ] 5.1.3 Function to serialize/deserialize manifests
- [ ] 5.2 Create `src/Urban_Amenities2/versioning/data_snapshot.py` with:
  - [ ] 5.2.1 DataSnapshot model (source_name, version, download_date, file_hash)
  - [ ] 5.2.2 Snapshot registration utilities
- [ ] 5.3 Implement run tracking storage (local JSONL or SQLite)
- [ ] 5.4 Add CLI commands for run management (`aucs run list`, `aucs run show`)
- [ ] 5.5 Write tests for versioning system

## 6. Logging & Error Handling

- [ ] 6.1 Configure structlog with JSON formatter for production
- [ ] 6.2 Create custom logger with context (run_id, stage, hex_id)
- [ ] 6.3 Define standard log levels and messages
- [ ] 6.4 Add performance logging utilities (timing decorators)
- [ ] 6.5 Create error classification system (data errors, computation errors, validation errors)

## 7. CLI Foundation

- [ ] 7.1 Create `src/Urban_Amenities2/cli/main.py` with Typer app
- [ ] 7.2 Add `aucs config validate <yaml>` command
- [ ] 7.3 Add `aucs config show` command to display loaded params
- [ ] 7.4 Add `aucs hex info <lat> <lon>` command for spatial debugging
- [ ] 7.5 Add `aucs run init` command to start new scoring run
- [ ] 7.6 Write tests for CLI commands

## 8. Integration & Documentation

- [ ] 8.1 Write `docs/architecture.md` explaining core systems
- [ ] 8.2 Write `docs/configuration.md` documenting all parameters
- [ ] 8.3 Create example parameter YAML in `configs/params_default.yml`
- [ ] 8.4 Add docstrings to all public functions
- [ ] 8.5 Create integration tests for the full parameter→schema pipeline
- [ ] 8.6 Update main README with setup instructions
