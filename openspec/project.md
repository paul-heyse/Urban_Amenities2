# Project Context

## Purpose

**AUCS 2.0 (Aker Urban Convenience Score)** is a comprehensive multi-modal accessibility scoring system that quantifies urban convenience for residents. Unlike simple walkability scores, AUCS measures what people can reach and how easily they can reach it across multiple transportation modes (walk, bike, transit, car), while accounting for destination quality, transit reliability, and seasonal factors.

**Project Goals:**

- Provide granular (250m hex) accessibility scores for Colorado, Utah, and Idaho
- Implement behavioral realism via nested logsum choice models
- Measure 7 key dimensions: Essentials, Leisure, Hubs/Airports, Jobs/Education, Transit Reliability, Trip-Chaining, and Seasonal Outdoors
- Enable regional comparisons and equity analysis
- Support urban planning, real estate analysis, and policy decisions

## Tech Stack

### Core Python Stack (3.11+)

- **Data Processing:** pandas, numpy, pyarrow, duckdb, polars (optional)
- **Geospatial:** geopandas, shapely>=2.0, pyproj, rtree, h3 (h3-py)
- **Raster/Climate:** xarray, rioxarray, rasterio
- **Math/Performance:** numba (JIT), scipy
- **Parallelization:** dask[dataframe] or ray (for large matrices)

### Routing & Transit

- **External Services:** OSRM (car/bike/foot), OpenTripPlanner 2 (transit)
- **GTFS Processing:** partridge, gtfs-kit
- **GTFS Realtime:** gtfs-realtime-bindings
- **HTTP Clients:** httpx, gql[requests] (for OTP GraphQL)

### Data Sources & APIs

- **Overture Maps:** Places (POIs), Transportation (networks)
- **Wikidata/Wikipedia:** SPARQLWrapper, qwikidata, requests (pageviews API)
- **NOAA Climate:** requests, pandas (Climate Normals API)
- **Transit Discovery:** Transitland API integration

### Engineering & Quality

- **Configuration:** pydantic>=2.0, pydantic-settings, ruamel.yaml
- **Validation:** pandera (schema checks on all tables)
- **Retries/Caching:** tenacity, backoff, diskcache, joblib, cachetools
- **Logging:** structlog (JSON logs for production)
- **CLI:** typer (command-line interface)
- **Testing:** pytest, hypothesis (property-based tests)
- **Orchestration:** prefect or apache-airflow (optional)

### Visualization (Optional)

- **Maps:** folium, pydeck, contextily
- **Charts:** matplotlib, plotnine, altair
- **Documentation:** mkdocs-material

### Development Tools

- **Linting:** ruff
- **Formatting:** black
- **Type Checking:** mypy (optional, Pydantic provides runtime validation)
- **Package Management:** micromamba (conda-forge)

## Project Conventions

### Code Style

**Python Style:**

- **PEP 8 compliant**, enforced by `ruff` and `black`
- **Line length:** 100 characters (configured in pyproject.toml)
- **Import order:** stdlib → third-party → local (enforced by ruff)
- **Naming:**
  - Functions/variables: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_SNAKE_CASE`
  - Private members: `_leading_underscore`
  - Module names: `lowercase_with_underscores`

**Type Hints:**

- Use Pydantic models for data structures and configuration
- Type hints on all public function signatures
- Runtime validation preferred over static typing (via Pydantic & Pandera)

**Docstrings:**

- All public functions, classes, and modules
- Google-style docstrings
- Include parameter types, return types, and brief examples for complex functions

**File Organization:**

- Keep modules under 500 lines; split if larger
- Keep functions under ~50 lines; extract helpers if longer
- One main responsibility per module

### Architecture Patterns

**Hexagonal (Ports & Adapters):**

- Core math/accessibility logic is pure (no I/O)
- I/O adapters in `io/` modules (Overture, GTFS, NOAA, etc.)
- Routing clients abstract external services (OSRM, OTP)

**Data Pipeline Pattern:**

1. **Ingest** → Raw data from external sources
2. **Enrich & Validate** → Apply schemas, deduplicate, hex-index
3. **Compute** → Apply mathematical models (GTC, logsum, CES, satiation)
4. **Aggregate** → Combine into subscores
5. **Normalize & Export** → Final AUCS output

**Functional Core, Imperative Shell:**

- Mathematical functions are pure (GTC, logsum, CES, satiation)
- Side effects (file I/O, API calls) isolated in separate modules
- Use dependency injection for routing clients and data loaders

**Configuration-Driven:**

- All parameters defined in YAML (600+ parameters)
- Loaded via Pydantic models with validation
- Parameter versioning via hash for reproducibility

**Schema-First:**

- Define Pandera schemas for all intermediate tables
- Validate on every pipeline stage
- Fail fast on schema violations

### Testing Strategy

**Unit Tests:**

- All mathematical kernels (GTC, logsum, CES, satiation, diversity)
- Property-based tests with `hypothesis` for mathematical invariants:
  - Monotonicity (more accessibility → higher scores)
  - Homogeneity (scale inputs → scale outputs proportionally)
  - Bounds (scores in valid ranges)
- Mock external services (OSRM, OTP, APIs)

**Integration Tests:**

- End-to-end pipeline tests on small synthetic datasets
- Verify data contracts (input schemas → output schemas)
- Check reproducibility (same params + data → same output)

**Test Coverage:**

- Maintain ≥95% line coverage and ≥90% branch coverage across first-party modules
- Prioritise historically flaky areas (I/O, routing, UI) to keep thresholds sustainable
- Use `pytest --cov --cov-branch` locally and review the CI coverage summary on every PR

**Test Organization:**

- `tests/unit/` for isolated unit tests
- `tests/integration/` for multi-component tests
- `tests/fixtures/` for shared test data

**Continuous Testing:**

- Run unit tests on every commit
- Run integration tests on PR
- Performance benchmarks on main branch

### Git Workflow

**Branching Strategy:**

- **`main`** - stable, deployable code
- **`cx/<short-description>`** - feature branches (following OpenSpec convention)
- Short-lived branches (< 1 week)
- One OpenSpec change per branch when possible

**Commit Conventions:**

- **Conventional Commits** format: `<type>(<scope>): <description>`
- Types: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`
- Scope: module or subscore (e.g., `feat(ea): add diversity bonus`)
- Keep commits atomic and focused
- Write descriptive commit messages (explain "why", not "what")

**Pull Request Process:**

1. Create PR from feature branch to `main`
2. Link to OpenSpec change proposal
3. Ensure all tests pass (`pytest -q`)
4. Ensure linting passes (`ruff check`, `black --check`)
5. Update tasks.md to mark completed tasks `[x]`
6. Request review
7. Squash merge to main
8. Delete feature branch after merge

**OpenSpec Integration:**

- Use `openspec archive <change>` after PR merge
- Keep specs/ directory in sync with implementations

## Domain Context

### Urban Accessibility Theory

**Behavioral Modeling:**

- Based on **random utility theory** and **discrete choice models**
- Travelers choose modes to maximize utility (minimize generalized cost)
- **Nested logsum** captures mode substitution within nests (non-motorized, transit, car)
- Time-of-day variation (peak vs off-peak accessibility)

**Key Concepts:**

- **Generalized Travel Cost (GTC):** Total perceived cost including time, wait, transfers, fares, reliability
- **Value of Time (VOT):** Converts fares to time equivalents ($18/hr weekday, $15/hr weekend)
- **Accessibility Weight (w_{i,a}):** Combined mode-choice-aware reachability from hex i to amenity a
- **CES Aggregation:** Constant Elasticity of Substitution models imperfect substitutes
- **Satiation:** Diminishing returns from many similar amenities

### Geographic Scope

**Primary Markets:**

- **Colorado:** Denver metro (RTD), Colorado Springs, Fort Collins, mountain resort towns
- **Utah:** Salt Lake City (UTA TRAX/FrontRunner), Provo-Orem, Ogden, Park City
- **Idaho:** Boise (Valley Regional Transit), Pocatello, Coeur d'Alene

**Spatial Resolution:**

- **H3 resolution 9:** ~250m average hex edge length
- Rationale: Balances walkable scale (~5 min walk) with computational tractability
- ~10,000 hexes per metro area

### Data Sources

**Primary Sources (see docs for full list):**

- Overture Maps (Places + Transportation)
- GTFS/GTFS-RT from 20+ agencies across CO/UT/ID
- NOAA Climate Normals (1991-2020)
- PAD-US (USGS Protected Areas)
- LODES (LEHD jobs data)
- NCES/IPEDS (schools and universities)
- FAA Airport Enplanements
- Wikidata/Wikipedia (popularity enrichment)

**Update Cadence:**

- Overture: Quarterly releases
- GTFS: Weekly or as agencies update
- GTFS-RT: Real-time (for reliability metrics)
- Jobs/Census: Annual
- Climate: Static (30-year normals)

## Important Constraints

### Performance Constraints

**Computational Scale:**

- ~1M hexes across CO/UT/ID
- ~500K POIs after deduplication
- ~100M OD pairs for accessibility matrices
- Target: Full state scoring in <6 hours on 16-core machine

**Memory Constraints:**

- Avoid loading full matrices into RAM; use chunked processing
- Use Parquet with compression for intermediate files
- Stream large datasets with Polars or DuckDB

**Routing Service Limits:**

- OSRM `/table` API: max 100×100 OD pairs per request (batch appropriately)
- OTP GraphQL: Rate limit queries, cache results

### Data Quality Constraints

**Overture Coverage:**

- Good for major metros, sparse in rural areas
- Supplement with state-specific sources (SNAP retailers for groceries, state childcare registries)

**GTFS Realtime Availability:**

- Not all agencies provide GTFS-RT
- Fallback to scheduled reliability proxies if unavailable

**Geocoding Accuracy:**

- Census blocks use centroids (not precise residential locations)
- PAD-US access points may need manual curation for trailheads

### Regulatory & Privacy

**No Personally Identifiable Information (PII):**

- All outputs are aggregated to 250m hexes
- No individual-level data (e.g., specific addresses)

**Data Licensing:**

- Respect Overture, GTFS, and API terms of use
- Transitland provides license metadata per feed; honor restrictions

**Open Source Intention:**

- Model equations and parameters are public
- Code should be open-source (MIT or Apache 2.0)
- Data outputs can be shared (aggregated hex-level scores)

## External Dependencies

### External Services (Must Be Running)

**OSRM (Open Source Routing Machine):**

- Purpose: Car, bike, foot routing over Overture networks
- Deployment: Docker container or dedicated server
- Profiles needed: `car`, `bike`, `foot`
- Build process: `osrm-extract`, `osrm-contract` on Overture segments
- API: HTTP REST (`/route`, `/table`)

**OpenTripPlanner 2 (OTP2):**

- Purpose: Transit routing with GTFS + street networks
- Deployment: JVM application (Docker or standalone)
- Graph build: GTFS feeds + Overture streets + elevation (optional)
- API: GraphQL (Transmodel endpoint)
- Resource requirements: ~8GB RAM per graph (metro-sized)

### External Data Sources

**Overture Maps:**

- Access: BigQuery public dataset or S3/Azure downloads
- Schema: <https://docs.overturemaps.org/>
- Licensing: CDLA Permissive 2.0

**Transitland v2 API:**

- Purpose: GTFS/GTFS-RT feed discovery and access
- Endpoint: <https://transit.land/api/v2/rest>
- API key required (free tier available)

**NOAA NCEI (Climate Normals):**

- Access: <https://www.ncei.noaa.gov/support/access-data-service-api-user-documentation>
- Dataset: `normals-monthly-1991-2020`
- No API key required

**Wikidata/Wikipedia:**

- SPARQL endpoint: <https://query.wikidata.org/sparql>
- Pageviews API: <https://wikimedia.org/api/rest_v1/>
- Rate limits: ~100 req/sec (be respectful)

**USGS PAD-US:**

- Access: ArcGIS FeatureServer or geodatabase download
- Endpoint: <https://www.usgs.gov/programs/gap-analysis-project/science/pad-us-data-download>

**Census LEHD LODES:**

- Access: Direct CSV downloads
- Endpoint: <https://lehd.ces.census.gov/data/>
- Version: Use LODES v8 (latest)

**FAA Airport Data:**

- Access: PDF/Excel download (annual)
- Endpoint: <https://www.faa.gov/airports/planning_capacity/passenger_allcargo_stats/>

### Key Libraries (Version Constraints)

**Critical:**

- `h3>=4.0` - H3 v4 API (breaking change from v3)
- `pydantic>=2.0` - Pydantic v2 (major rewrite)
- `shapely>=2.0` - Significant speedups in v2
- `geopandas>=0.14` - For Shapely 2 compatibility
- `pyarrow>=14.0` - For Parquet schema evolution

**Pin Major Versions:**

- See `pyproject.toml` for complete dependency specification
- Use `micromamba` or `conda-forge` for geospatial packages
- Test with pinned versions; update cautiously

---

**For Implementation Details:**

- See `openspec/IMPLEMENTATION_GUIDE.md` for phase-by-phase roadmap
- See `openspec/CHANGES_SUMMARY.md` for change proposal summaries
- See `docs/Urban_Amenities_Model_Spec.sty` for mathematical specification
