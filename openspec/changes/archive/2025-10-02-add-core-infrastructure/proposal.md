# Core Infrastructure for AUCS 2.0

## Why

The AUCS 2.0 (Aker Urban Convenience Score) model requires foundational infrastructure to manage spatial computations, parameters, and configuration. This change establishes the core systems that all other model components will build upon, including:

- Type-safe parameter management from YAML specifications
- H3 hexagonal grid operations at 250m resolution
- Data versioning and reproducibility tracking
- Base data structures for spatial operations

Without this foundation, we cannot implement the mathematical model specified in equations E1-E39.

## What Changes

- Create Pydantic models mirroring the complete parameter specification (grid, modes, nests, categories, subscores, etc.)
- Implement H3 r=9 (≈250m) grid operations for all spatial joins and aggregations
- Build parameter loading, validation, and versioning system
- Create base data schemas (hexes, POIs, networks, travel times)
- Implement reproducibility tracking (run manifests, data snapshot IDs, parameter hashes)
- Set up logging and configuration management
- **BREAKING**: Establishes new project architecture and dependency requirements

## Impact

- Affected specs: `core-infrastructure`, `spatial-grid`, `parameter-management` (all new)
- Affected code: Creates `src/Urban_Amenities2/` with modules:
  - `config/` - Pydantic models and parameter loading
  - `hex/` - H3 utilities and spatial operations
  - `schemas/` - Data contracts and validation
  - `versioning/` - Run tracking and reproducibility
- Dependencies: Adds h3, pydantic, ruamel.yaml, pandera, structlog, typer
- Foundation for ALL subsequent model components
