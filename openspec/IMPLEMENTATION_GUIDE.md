# AUCS 2.0 Implementation Guide

This document provides a comprehensive overview of the OpenSpec change proposals for implementing the Aker Urban Convenience Score (AUCS) 2.0 model.

## Overview

AUCS 2.0 quantifies urban convenience by measuring multi-modal accessibility to amenities, transit reliability, jobs/education reach, and major hub connectivity. The model operates on a 250m hexagonal grid (H3 resolution 9) and implements behavioral realism via nested logsum accessibility.

**Geographic Scope:** Colorado, Utah, and Idaho
**Mathematical Specification:** 39 equations (E1-E39) covering generalized cost, logsums, quality scoring, and 7 subscores

## Implementation Architecture

The implementation is decomposed into **15 change proposals**, each representing a logical capability or subscore. Changes have dependencies and should be implemented in the order specified below.

## Change Proposals

### **Phase 1: Foundation** (Weeks 1-3)

#### 1. `add-core-infrastructure` ✓ VALIDATED

**Purpose:** Establish parameter management, H3 spatial grid, data schemas, versioning, and CLI
**Key Outputs:**

- Pydantic models for all 600+ parameters from the YAML spec
- H3 resolution 9 operations (indexing, aggregation, neighbors)
- Data validation schemas (Pandera)
- Run manifest and reproducibility tracking
- CLI foundation (`aucs config`, `aucs hex`, `aucs run`)

**Dependencies:** None (foundational)
**Modules:** `config/`, `hex/`, `schemas/`, `versioning/`, `cli/`

---

#### 2. `add-data-ingestion` ✓ VALIDATED

**Purpose:** Ingest all external data sources and index to H3 hexes
**Key Outputs:**

- Overture Places with category crosswalk (50+ AUCS categories)
- Overture Transportation segments for routing
- GTFS static/RT for CO/UT/ID transit agencies
- NOAA Climate Normals for seasonal comfort
- PAD-US parks, USFS trails, LODES jobs, NCES schools, IPEDS universities
- FAA airports, Wikidata/Wikipedia enrichment
- POI deduplication and hex indexing

**Dependencies:** `add-core-infrastructure` (requires H3, schemas, versioning)
**Modules:** `io/overture/`, `io/gtfs/`, `io/climate/`, `io/parks/`, `io/jobs/`, `io/education/`, `io/enrichment/`, `xwalk/`, `dedupe/`

**Data Outputs:**

- `data/processed/pois.parquet` (hex-indexed POIs with aucstype, Q_a attributes)
- `data/processed/gtfs_*.parquet` (stops, routes, headways, reliability)
- `data/processed/parks.parquet`, `jobs_by_hex.parquet`, `schools.parquet`, etc.

---

#### 3. `add-routing-engines`

**Purpose:** Integrate OSRM (car/bike/foot) and OTP2 (transit) for travel time computation
**Key Outputs:**

- OSRM graph builds from Overture Transportation (3 profiles)
- OTP2 graph build from GTFS + Overture streets
- HTTP/GraphQL clients for routing APIs
- Unified routing interface
- Batched travel time matrix computation

**Dependencies:** `add-data-ingestion` (requires network segments, GTFS)
**Modules:** `router/osrm.py`, `router/otp.py`, `router/api.py`, `router/batch.py`, `router/cache.py`

**Data Outputs:**

- `data/processed/skims_{car,bike,foot}_{period}.parquet`
- `data/processed/skims_transit_{period}.parquet`

---

### **Phase 2: Accessibility Core** (Weeks 4-5)

#### 4. `add-travel-time-computation`

**Purpose:** Implement generalized travel cost (GTC) and nested logsum accessibility (E1-E5)
**Key Outputs:**

- GTC computation: in-vehicle time, wait, transfers, reliability buffers, fares, carry penalties
- Mode utility functions with decay and constants
- Nested logsum (non-motorized, transit, car nests)
- Time-slice weighted aggregation
- Accessibility weight w_{i,a} for all hex-POI pairs

**Dependencies:** `add-routing-engines`, `add-data-ingestion`
**Modules:** `math/gtc.py`, `math/logsum.py`, `math/decay.py`, `accessibility/matrices.py`, `accessibility/weights.py`

**Mathematical Core:** Equations E1-E5
**Data Outputs:**

- `data/processed/accessibility_poi.parquet` (hex × POI × w_{i,a})
- `data/processed/accessibility_jobs.parquet` (hex × block × w_{i,block})

---

#### 5. `add-amenity-quality`

**Purpose:** Compute destination quality Q_a, diversity, and novelty (E6-E9)
**Key Outputs:**

- Quality scoring: size, capacity, popularity (Wikipedia pageviews), brand, heritage
- Brand-proximity deduplication weight (E8)
- Opening hours bonus
- Q_a merged into POIs

**Dependencies:** `add-data-ingestion` (requires Wikidata enrichment)
**Modules:** `quality/scoring.py`, `quality/dedupe.py`, `quality/popularity.py`

**Mathematical Core:** Equations E6-E9

---

#### 6. `add-category-aggregation`

**Purpose:** Implement CES aggregation and satiation curves (E10-E12)
**Key Outputs:**

- CES aggregator with elasticity ρ_c
- Satiation curves: S_c = 100 · (1 - exp(-κ_c · V_c))
- Anchor-based κ computation
- Within-category diversity bonuses (E13)

**Dependencies:** `add-amenity-quality`, `add-travel-time-computation`
**Modules:** `math/ces.py`, `math/satiation.py`, `math/diversity.py`

**Mathematical Core:** Equations E10-E13

---

### **Phase 3: Subscores** (Weeks 6-10)

#### 7. `add-essentials-access` ✓ VALIDATED

**Purpose:** Essentials Access (EA) subscore (E14-E15) - 30% weight
**Categories:** grocery, pharmacy, primary_care, childcare, K8_school, bank_atm, postal_parcel
**Outputs:** `data/processed/scores_ea.parquet`

**Dependencies:** `add-category-aggregation`

---

#### 8. `add-leisure-culture-access`

**Purpose:** Leisure & Culture Access (LCA) subscore (E16-E18) - 18% weight
**Categories:** restaurants, cafes, bars, cinemas, performing_arts, museums_galleries, parks_trails, sports_rec
**Special Features:** Cross-category CES, novelty bonus from pageview volatility
**Outputs:** `data/processed/scores_lca.parquet`

**Dependencies:** `add-category-aggregation`

---

#### 9. `add-hub-airport-access`

**Purpose:** Major Urban Hub & Airport Access (MUHAA) subscore (E19-E25) - 16% weight
**Components:**

- Hub mass (population, GDP, POI density, culture)
- Best transit/car access to CBSAs
- Airport connectivity weighted by enplanements
- Decay by generalized travel cost

**Outputs:** `data/processed/scores_muhaa.parquet`

**Dependencies:** `add-travel-time-computation`, `add-data-ingestion` (FAA airports, BEA/Census hubs)

---

#### 10. `add-jobs-education-access`

**Purpose:** Jobs & Education Access (JEA) subscore (E26-E27) - 14% weight
**Components:**

- LODES jobs gravity with optional industry weights
- University accessibility weighted by Carnegie tier
- Nested logsum accessibility to jobs and universities

**Outputs:** `data/processed/scores_jea.parquet`

**Dependencies:** `add-travel-time-computation`, `add-data-ingestion` (LODES, IPEDS)

---

#### 11. `add-mobility-reliability`

**Purpose:** Mobility Options, Reliability & Resilience (MORR) subscore (E28-E33) - 12% weight
**5 Components:**

1. Frequent transit exposure (C₁)
2. Service span (C₂)
3. On-time reliability (C₃) from GTFS-RT
4. Network redundancy (C₄) - transit and road alternatives
5. Micromobility presence (C₅) from GBFS

**Outputs:** `data/processed/scores_morr.parquet`

**Dependencies:** `add-data-ingestion` (GTFS-RT, GBFS), `add-routing-engines`

---

#### 12. `add-corridor-enrichment`

**Purpose:** Corridor Trip-Chaining Enrichment (CTE) subscore (E34-E35) - 5% weight
**Method:**

- Identify top 2 transit paths from hex to CBD/hub
- Buffer stops by 350m, collect POIs
- Score 2-stop errand chains (grocery+pharmacy, etc.)
- Require minimal detour (≤10 min)

**Outputs:** `data/processed/scores_cte.parquet`

**Dependencies:** `add-routing-engines` (OTP2 paths), `add-data-ingestion` (transit, POIs)

---

#### 13. `add-seasonal-outdoors`

**Purpose:** Seasonal Outdoors Usability (SOU) subscore (E36) - 5% weight
**Method:**

- Multiply parks/trails score by climate comfort scalar σ_out
- σ_out from NOAA normals: comfortable temperature, low precip, manageable wind

**Outputs:** `data/processed/scores_sou.parquet`

**Dependencies:** `add-data-ingestion` (climate, parks), `add-category-aggregation` (parks scoring)

---

### **Phase 4: Aggregation & Output** (Week 11)

#### 14. `add-score-aggregation`

**Purpose:** Normalize subscores and compute final AUCS (E37-E39)
**Key Outputs:**

- Metro-relative percentile normalization (P5-P95) per equation E38
- Standards-based anchor normalization (E39) for cross-metro comparability
- Weighted sum: AUCS = Σ w_k · S_k where weights sum to 100
- Explainability: top contributors per hex (amenities, modes, paths)
- Final output files and QA reports

**Dependencies:** All subscore changes
**Modules:** `scores/normalization.py`, `scores/aggregation.py`, `scores/explainability.py`, `export/`

**Data Outputs:**

- `output/aucs.parquet` (hex_id, AUCS, all subscores, metadata)
- `output/explainability.parquet` (top contributors JSON per hex)
- `output/summary_stats.json`
- `output/qa_report.html`

---

### **Phase 5: Advanced Features** (Week 12+)

#### 15. `add-explainability`

**Purpose:** Detailed visualization and attribution tools
**Features:**

- Hex choropleths (folium/pydeck maps)
- Subscore distribution plots
- Per-hex drill-down: show top POIs, best modes, contributing paths
- Calibration utilities and sensitivity analysis
- Comparison across metros

**Dependencies:** `add-score-aggregation`

---

## Dependency Graph

```
add-core-infrastructure
    ├── add-data-ingestion
    │   ├── add-routing-engines
    │   │   ├── add-travel-time-computation
    │   │   │   ├── add-amenity-quality
    │   │   │   │   ├── add-category-aggregation
    │   │   │   │   │   ├── add-essentials-access
    │   │   │   │   │   ├── add-leisure-culture-access
    │   │   │   │   │   └── add-seasonal-outdoors
    │   │   │   │   ├── add-hub-airport-access
    │   │   │   │   ├── add-jobs-education-access
    │   │   │   │   └── add-corridor-enrichment
    │   │   │   └── add-mobility-reliability
    │   └── (used by most changes)
    └── (foundation for all)
```

**Critical Path:** 1 → 2 → 3 → 4 → 5 → 6 → {7-13} → 14 → 15

---

## Implementation Order

1. **Week 1-3:** Phase 1 (Foundation) - changes 1-3
2. **Week 4-5:** Phase 2 (Accessibility Core) - changes 4-6
3. **Week 6-10:** Phase 3 (Subscores) - changes 7-13 (can parallelize)
4. **Week 11:** Phase 4 (Aggregation) - change 14
5. **Week 12+:** Phase 5 (Advanced) - change 15

**Note:** Subscores (changes 7-13) can be implemented in parallel once changes 1-6 are complete.

---

## Data Flow Summary

```
External Sources
    ↓
[add-data-ingestion] → pois.parquet, gtfs_*.parquet, climate.parquet, ...
    ↓
[add-routing-engines] → skims_{mode}_{period}.parquet
    ↓
[add-travel-time-computation] → accessibility_poi.parquet (w_{i,a})
    ↓
[add-amenity-quality] → pois.parquet with Q_a
    ↓
[add-category-aggregation] → CES + satiation functions
    ↓
[Subscore Changes] → scores_{ea,lca,muhaa,jea,morr,cte,sou}.parquet
    ↓
[add-score-aggregation] → output/aucs.parquet (FINAL)
```

---

## Mathematical Equations Mapping

| Equations | Change | Purpose |
|-----------|--------|---------|
| E1-E5 | add-travel-time-computation | GTC, nested logsum, w_{i,a} |
| E6-E9 | add-amenity-quality | Q_a, deduplication |
| E10-E13 | add-category-aggregation | CES, satiation, diversity |
| E14-E15 | add-essentials-access | EA subscore |
| E16-E18 | add-leisure-culture-access | LCA subscore |
| E19-E25 | add-hub-airport-access | MUHAA subscore |
| E26-E27 | add-jobs-education-access | JEA subscore |
| E28-E33 | add-mobility-reliability | MORR subscore |
| E34-E35 | add-corridor-enrichment | CTE subscore |
| E36 | add-seasonal-outdoors | SOU subscore |
| E37-E39 | add-score-aggregation | Normalization, final AUCS |

---

## Key Technologies

- **Spatial:** h3, geopandas, shapely, pyproj, rtree
- **Data:** pandas, polars, duckdb, pyarrow, numpy
- **Math:** numba, scipy
- **Routing:** OSRM (external), OTP2 (external), httpx, gql
- **Transit:** partridge, gtfs-kit, gtfs-realtime-bindings
- **Climate:** xarray, rasterio
- **Config:** pydantic, ruamel.yaml
- **Quality:** pandera, pytest
- **CLI:** typer
- **Logging:** structlog

---

## Getting Started

1. **Review this guide** to understand the change structure
2. **Read** `openspec/AGENTS.md` for OpenSpec workflow
3. **Start with** `add-core-infrastructure`:
   - Review `proposal.md`, `tasks.md`, spec files
   - Implement tasks sequentially
   - Mark tasks complete as you go
   - Validate: `openspec validate add-core-infrastructure --strict`
4. **Move to** `add-data-ingestion` once core is complete
5. **Follow** the dependency order above

---

## Validation Commands

```bash
# List all changes
openspec list

# Show change details
openspec show add-core-infrastructure

# Validate a change
openspec validate add-core-infrastructure --strict

# Show change diff (what specs will change)
openspec diff add-core-infrastructure

# After implementation, archive the change
openspec archive add-core-infrastructure
```

---

## Questions?

- Review the mathematical specification in `docs/Urban_Amenities_Model_Spec.sty`
- Review data sources in `docs/urban_amenity_data_source_mapping`
- Review API mappings in `docs/Urban Amenities API to parameter mapping.md`
- Review category crosswalk in `docs/AUCS place category crosswalk`
- Consult OpenSpec documentation in `openspec/AGENTS.md`
