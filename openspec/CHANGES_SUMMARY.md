# AUCS 2.0 OpenSpec Changes Summary

## Overview

I've created **6 comprehensive OpenSpec change proposals** that establish the foundation and key components for implementing the AUCS 2.0 (Aker Urban Convenience Score) model. These changes cover approximately 70% of the complete system, with the remaining subscore implementations following the same pattern.

---

## Created Change Proposals

### ✅ 1. `add-core-infrastructure` (VALIDATED)

**Status:** Complete with 40 tasks
**Purpose:** Establishes the foundational infrastructure

**What it provides:**

- Type-safe parameter management (600+ parameters from YAML spec)
- H3 spatial grid operations at 250m resolution (r=9)
- Data schemas and validation (Pandera)
- Run reproducibility tracking and versioning
- CLI foundation and structured logging

**Key deliverables:**

- Pydantic models mirroring the entire parameter specification
- H3 hex operations: indexing, aggregation, neighbors, distance
- Base data contracts for POIs, networks, travel times, scores
- Run manifests with parameter hashing
- CLI commands: `aucs config`, `aucs hex`, `aucs run`

---

### ✅ 2. `add-data-ingestion` (VALIDATED)

**Status:** Complete with 48 tasks
**Purpose:** Ingests all external data sources and indexes to H3 hexes

**What it provides:**

- **Overture Places:** 50+ AUCS categories via prefix-based crosswalk
- **Overture Transportation:** Road/bike/pedestrian networks for routing
- **GTFS Static/Realtime:** All CO/UT/ID transit agencies
- **Climate Data:** NOAA normals for seasonal comfort scoring
- **Parks & Recreation:** PAD-US, USFS trails, NPS, RIDB
- **Jobs & Education:** LODES employment, NCES schools, IPEDS universities
- **Airports:** FAA enplanements for connectivity weighting
- **Enrichment:** Wikidata/Wikipedia for popularity and capacity

**Key deliverables:**

- `data/processed/pois.parquet` - hex-indexed POIs with aucstype, Q_a attributes
- `data/processed/gtfs_*.parquet` - stops, routes, headways, reliability metrics
- `data/processed/parks.parquet`, `jobs_by_hex.parquet`, `schools.parquet`, etc.
- POI deduplication using brand-proximity and fuzzy name matching
- Snapshot tracking and incremental update mechanisms

---

### ✅ 3. `add-routing-engines`

**Status:** Complete with 26 tasks
**Purpose:** Integrates OSRM and OTP2 for multi-modal travel time computation

**What it provides:**

- **OSRM:** Car/bike/foot routing over Overture networks
- **OTP2:** Transit routing with GTFS + street networks
- Unified routing API abstracting engine differences
- Batched many-to-many matrix computation
- Travel time caching with version tracking

**Key deliverables:**

- OSRM graph builds (3 profiles: car, bike, foot)
- OTP2 graph build (GTFS + Overture streets per market)
- HTTP/GraphQL clients for both engines
- `data/processed/skims_{mode}_{period}.parquet` - travel time matrices

---

### ✅ 4. `add-travel-time-computation`

**Status:** Complete with 29 tasks
**Purpose:** Implements the mathematical core (equations E1-E5)

**What it provides:**

- **Generalized Travel Cost (E1):** In-vehicle time, wait, transfers, reliability buffers, fares, carry penalties
- **Mode Utilities (E2):** Decay functions, mode constants, comfort factors
- **Nested Logsum (E3-E4):** Non-motorized/transit/car nests with log-sum-exp stability
- **Time-Slice Aggregation (E5):** Weighted accessibility w_{i,a} across time periods

**Key deliverables:**

- Vectorized GTC and logsum computations (NumPy + Numba JIT)
- Accessibility matrix builders: hex-to-POI, hex-to-job, hex-to-hub
- `data/processed/accessibility_poi.parquet` - w_{i,a} for all OD pairs
- Numerical stability handling (overflow, underflow, unreachable destinations)

---

### ✅ 5. `add-essentials-access` (VALIDATED)

**Status:** Complete with 31 tasks
**Purpose:** Implements Essentials Access (EA) subscore (30% weight, E14-E15)

**What it provides:**

- CES aggregation within 7 essential categories
- Satiation curves with anchor-based calibration
- Within-category diversity bonuses (Shannon entropy)
- Shortfall penalty for missing critical services

**Essential categories:**

- grocery, pharmacy, primary_care, childcare, K8_school, bank_atm, postal_parcel

**Key deliverables:**

- `data/processed/scores_ea.parquet` - EA scores per hex
- Top contributing POIs per category for explainability
- Calibration utilities for parameter sensitivity

---

### ✅ 6. `add-score-aggregation`

**Status:** Complete with 32 tasks
**Purpose:** Normalizes subscores and computes final AUCS (E37-E39)

**What it provides:**

- Metro-relative percentile normalization (P5-P95 clamping)
- Standards-based anchor normalization for cross-metro comparability
- Weighted aggregation: AUCS = Σ w_k · S_k
- Explainability artifacts (top contributors per hex)
- QA reports and visualizations

**Key deliverables:**

- `output/aucs.parquet` - Final scores with all subscores
- `output/explainability.parquet` - Top contributing POIs, modes, paths
- `output/summary_stats.json` - Distribution statistics
- `output/qa_report.html` - Hex choropleths and subscore correlations

---

## What's Covered vs. What Remains

### ✅ Covered (6 changes, ~70% of system)

1. **Foundation:** Parameters, H3 grid, versioning, CLI
2. **Data:** All ingestion pipelines (Overture, GTFS, climate, parks, jobs, education)
3. **Routing:** OSRM + OTP2 integration
4. **Accessibility Core:** GTC, nested logsum, w_{i,a} computation
5. **One Complete Subscore:** Essentials Access (EA) as template
6. **Final Output:** Normalization, aggregation, explainability

### 📋 Remaining (9 subscore changes, ~30% of system)

Following the same pattern as Essentials Access:

7. **add-amenity-quality** - Q_a scoring, diversity, novelty (E6-E9)
8. **add-category-aggregation** - CES and satiation utilities (E10-E13)
9. **add-leisure-culture-access** - LCA subscore (E16-E18)
10. **add-hub-airport-access** - MUHAA subscore (E19-E25)
11. **add-jobs-education-access** - JEA subscore (E26-E27)
12. **add-mobility-reliability** - MORR subscore with 5 components (E28-E33)
13. **add-corridor-enrichment** - CTE trip-chaining subscore (E34-E35)
14. **add-seasonal-outdoors** - SOU climate-weighted subscore (E36)
15. **add-explainability** - Advanced visualization and attribution tools

---

## How the Changes Fit Together

### Dependency Flow

```
add-core-infrastructure (foundation)
    ↓
add-data-ingestion (all external data)
    ↓
add-routing-engines (OSRM + OTP2)
    ↓
add-travel-time-computation (GTC, logsum, w_{i,a})
    ↓
add-amenity-quality + add-category-aggregation
    ↓
[All Subscore Changes] (can be parallel)
    ↓
add-score-aggregation (final AUCS)
    ↓
add-explainability (visualization)
```

### Mathematical Coverage

- **E1-E5:** ✅ add-travel-time-computation
- **E6-E9:** 📋 add-amenity-quality
- **E10-E13:** 📋 add-category-aggregation (but used in EA)
- **E14-E15:** ✅ add-essentials-access
- **E16-E36:** 📋 6 remaining subscore changes
- **E37-E39:** ✅ add-score-aggregation

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-3) ✅ READY

1. Implement `add-core-infrastructure`
2. Implement `add-data-ingestion`
3. Set up OSRM and OTP2 external services

### Phase 2: Accessibility Core (Weeks 4-5) ✅ READY

4. Implement `add-routing-engines`
5. Implement `add-travel-time-computation`
6. Implement `add-amenity-quality` and `add-category-aggregation`

### Phase 3: Subscores (Weeks 6-10) - Parallel after Phase 2

7. Implement remaining subscores using `add-essentials-access` as template:
   - LCA, MUHAA, JEA, MORR, CTE, SOU

### Phase 4: Output (Week 11) ✅ READY

8. Implement `add-score-aggregation`

### Phase 5: Polish (Week 12+)

9. Implement `add-explainability`
10. Calibration and validation

---

## File Structure Created

```
openspec/
├── IMPLEMENTATION_GUIDE.md          # Comprehensive guide (this is the master doc)
├── CHANGES_SUMMARY.md              # This summary
├── changes/
│   ├── add-core-infrastructure/    # ✅ 40 tasks
│   │   ├── proposal.md
│   │   ├── tasks.md
│   │   └── specs/
│   │       ├── core-infrastructure/spec.md
│   │       ├── spatial-grid/spec.md
│   │       └── parameter-management/spec.md
│   ├── add-data-ingestion/         # ✅ 48 tasks
│   │   ├── proposal.md
│   │   ├── tasks.md
│   │   └── specs/
│   │       ├── overture-places/spec.md
│   │       ├── overture-transportation/spec.md
│   │       ├── gtfs-integration/spec.md
│   │       ├── climate-data/spec.md
│   │       ├── parks-recreation/spec.md
│   │       └── jobs-education-data/spec.md
│   ├── add-routing-engines/        # ✅ 26 tasks
│   ├── add-travel-time-computation/ # ✅ 29 tasks
│   ├── add-essentials-access/      # ✅ 31 tasks (TEMPLATE FOR OTHER SUBSCORES)
│   └── add-score-aggregation/      # ✅ 32 tasks
```

**Total: 206 implementation tasks across 6 changes**

---

## Next Steps

### 1. Review the Proposals

Start with `openspec/IMPLEMENTATION_GUIDE.md` for the big picture, then review individual change proposals:

```bash
cd /home/paul/Urban_Amenities2

# View all changes
openspec list

# Read a specific change
openspec show add-core-infrastructure

# View change diff (what specs will be created)
openspec diff add-core-infrastructure

# Validate all changes
openspec validate add-core-infrastructure --strict
```

### 2. Begin Implementation

Follow the dependency order. Start with `add-core-infrastructure`:

1. Read `proposal.md` to understand why and what
2. Read `tasks.md` to see the step-by-step plan
3. Read spec files to understand requirements and scenarios
4. Implement tasks sequentially
5. Mark tasks complete: edit `tasks.md` and change `- [ ]` to `- [x]`
6. Test and validate as you go

### 3. After Each Change is Implemented

```bash
# Archive the change (moves it to changes/archive/ and updates specs/)
openspec archive add-core-infrastructure

# The specs/ directory will be populated with the requirements
```

### 4. Create Remaining Subscore Changes

Use `add-essentials-access` as a template for the 6 remaining subscores. The pattern is:

- Load POIs and accessibility weights for subscore categories
- Apply CES + satiation
- Add subscore-specific logic (novelty for LCA, shortfall for EA, etc.)
- Write scores and explainability

---

## Key Documents Reference

### In This Repo

- **`openspec/IMPLEMENTATION_GUIDE.md`** - Master guide (START HERE)
- **`openspec/CHANGES_SUMMARY.md`** - This summary
- **`openspec/AGENTS.md`** - OpenSpec workflow rules
- **`docs/Urban_Amenities_Model_Spec.sty`** - Mathematical specification (E1-E39)
- **`docs/urban_amenity_data_source_mapping`** - Data sources to parameters
- **`docs/Urban Amenities API to parameter mapping.md`** - API endpoints
- **`docs/AUCS place category crosswalk`** - Overture→AUCS categories

### OpenSpec Commands

```bash
openspec list                        # List all changes
openspec list --specs                # List specs (empty until archiving)
openspec show <change>               # Show change details
openspec diff <change>               # Show what will change
openspec validate <change> --strict  # Validate before implementing
openspec archive <change>            # Archive after implementing
```

---

## Questions or Issues?

1. **OpenSpec workflow unclear?** → Read `openspec/AGENTS.md`
2. **Mathematical equations unclear?** → Read `docs/Urban_Amenities_Model_Spec.sty`
3. **Data sources unclear?** → Read `docs/urban_amenity_data_source_mapping`
4. **Implementation approach unclear?** → Read `openspec/IMPLEMENTATION_GUIDE.md`
5. **Specific change unclear?** → Read the change's `proposal.md` and `tasks.md`

---

## Summary Statistics

- **6 change proposals created** (4 foundational + 1 subscore template + 1 output)
- **206 implementation tasks defined**
- **15 new capabilities specified** (3 in core-infrastructure, 6 in data-ingestion, 3 in routing, 1 in each other change, plus supporting specs)
- **39 mathematical equations mapped** (E1-E39 → specific changes)
- **3 changes fully validated** (add-core-infrastructure, add-data-ingestion, add-essentials-access)
- **~70% of system architecture defined**

The foundation is complete. The remaining 9 changes (subscore implementations) follow established patterns and can be created as needed during implementation.
