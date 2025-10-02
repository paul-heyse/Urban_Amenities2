# AUCS 2.0 Implementation with OpenSpec

This repository contains the OpenSpec-driven implementation plan for the **Aker Urban Convenience Score (AUCS) 2.0** model—a sophisticated multi-modal accessibility scoring system for urban environments.

## 🚀 Quick Start

### 1. Understand the System

Read the documentation in order:

1. **`docs/Urban Amenities Model Overview.md`** - Conceptual overview
2. **`docs/Urban_Amenities_Model_Spec.sty`** - Mathematical specification (39 equations)
3. **`openspec/IMPLEMENTATION_GUIDE.md`** - Implementation roadmap ⭐ **START HERE FOR IMPLEMENTATION**
4. **`openspec/CHANGES_SUMMARY.md`** - What's been created so far

### 2. Explore the Change Proposals

```bash
# List all proposed changes
openspec list

# View details of a specific change
openspec show add-core-infrastructure

# See what specifications will be created
openspec diff add-core-infrastructure

# Validate a change
openspec validate add-core-infrastructure --strict
```

### 3. Begin Implementation

Follow the dependency order in `openspec/IMPLEMENTATION_GUIDE.md`:

```
Phase 1: Foundation
  → add-core-infrastructure (40 tasks)
  → add-data-ingestion (48 tasks)
  → add-routing-engines (26 tasks)

Phase 2: Accessibility Core
  → add-travel-time-computation (29 tasks)
  → add-amenity-quality
  → add-category-aggregation

Phase 3: Subscores (can parallelize)
  → add-essentials-access (31 tasks) ← TEMPLATE
  → add-leisure-culture-access
  → add-hub-airport-access
  → add-jobs-education-access
  → add-mobility-reliability
  → add-corridor-enrichment
  → add-seasonal-outdoors

Phase 4: Output
  → add-score-aggregation (32 tasks)

Phase 5: Visualization
  → add-explainability
```

## 📚 What is AUCS 2.0?

The Aker Urban Convenience Score quantifies **what residents can reach** and **how easily they can reach it** across multiple modes of transportation. It's different from simple "walkability" scores because it:

- Models **multi-modal accessibility** (walk, bike, transit, car)
- Incorporates **behavioral realism** via nested logsum choice models
- Accounts for **destination quality, diversity, and novelty**
- Measures **transit reliability and resilience** from real-time data
- Includes **regional connectivity** (major hubs, airports)
- Adapts to **seasonal climate** conditions

### Spatial Unit

**H3 hexagons** at resolution 9 (~250m edge length)

### Geographic Scope

**Colorado, Utah, and Idaho** (expandable to other regions)

### Seven Subscores (weighted sum → AUCS)

1. **Essentials Access (EA)** - 30% - Daily needs (grocery, pharmacy, healthcare, childcare, schools)
2. **Leisure & Culture Access (LCA)** - 18% - Restaurants, arts, parks, recreation
3. **Major Urban Hub & Airport Access (MUHAA)** - 16% - Connectivity to major cities and airports
4. **Jobs & Education Access (JEA)** - 14% - Employment and universities
5. **Mobility Options, Reliability & Resilience (MORR)** - 12% - Transit quality and alternatives
6. **Corridor Trip-Chaining Enrichment (CTE)** - 5% - Errand-chaining convenience
7. **Seasonal Outdoors Usability (SOU)** - 5% - Climate-adjusted parks/trails access

## 🗂️ Repository Structure

```
Urban_Amenities2/
├── openspec/
│   ├── IMPLEMENTATION_GUIDE.md      ⭐ Master implementation guide
│   ├── CHANGES_SUMMARY.md           📊 Summary of created changes
│   ├── AGENTS.md                    📖 OpenSpec workflow rules
│   ├── project.md                   📝 Project conventions (to be filled)
│   ├── changes/                     🔧 Active change proposals
│   │   ├── add-core-infrastructure/
│   │   ├── add-data-ingestion/
│   │   ├── add-routing-engines/
│   │   ├── add-travel-time-computation/
│   │   ├── add-essentials-access/
│   │   └── add-score-aggregation/
│   └── specs/                       📜 Deployed specifications (empty until archiving)
├── docs/
│   ├── Urban Amenities Model Overview.md
│   ├── Urban_Amenities_Model_Spec.sty         # Mathematical equations E1-E39
│   ├── urban_amenity_data_source_mapping      # Data sources
│   ├── Urban Amenities API to parameter mapping.md
│   └── AUCS place category crosswalk          # Overture→AUCS categories
├── src/Urban_Amenities2/            # Implementation (to be created)
├── tests/                           # Tests (to be created)
├── data/                            # Data pipelines (to be created)
└── configs/                         # Parameter YAML files (to be created)
```

## 📋 Current Status

### ✅ Complete (6 change proposals, 206 tasks)

1. **add-core-infrastructure** - Parameters, H3 grid, versioning, CLI (40 tasks)
2. **add-data-ingestion** - All data sources ingestion (48 tasks)
3. **add-routing-engines** - OSRM + OTP2 integration (26 tasks)
4. **add-travel-time-computation** - GTC, nested logsum (29 tasks)
5. **add-essentials-access** - EA subscore template (31 tasks)
6. **add-score-aggregation** - Normalization and final AUCS (32 tasks)

### 📝 Remaining (9 changes)

7-14. Six subscore implementations (follow EA template)
15. Explainability and visualization tools

**Progress: ~70% of architecture defined**

## 🔑 Key Technologies

- **Spatial:** H3, GeoPandas, Shapely, PyProj
- **Data:** Pandas, Polars, DuckDB, PyArrow, NumPy
- **Math:** NumPy, SciPy, Numba (JIT compilation)
- **Routing:** OSRM (external), OpenTripPlanner 2 (external)
- **Transit:** Partridge, GTFS-Kit, GTFS-Realtime-Bindings
- **Config:** Pydantic, ruamel.yaml
- **Quality:** Pandera (validation), pytest
- **CLI:** Typer
- **Logging:** structlog

## 📊 Data Sources

### Primary Sources

- **Overture Maps** - Places (POIs) + Transportation (networks)
- **GTFS/GTFS-RT** - Transit schedules and realtime (CO/UT/ID agencies)
- **NOAA** - Climate normals (1991-2020)
- **PAD-US** - Protected areas and parks (USGS)
- **USFS/NPS** - Trails and recreation sites
- **LODES** - Jobs data (LEHD/Census)
- **NCES/IPEDS** - Schools and universities
- **FAA** - Airport enplanements
- **Wikidata/Wikipedia** - Popularity and venue enrichment

### Geographic Coverage

- **Colorado:** RTD Denver, CDOT Bustang, 15+ local agencies
- **Utah:** UTA (TRAX, FrontRunner), Cache Valley, Park City, St. George
- **Idaho:** Valley Regional Transit (Boise), Pocatello, Coeur d'Alene

## 🎯 How to Work with OpenSpec

### OpenSpec Workflow (3 Stages)

#### Stage 1: Creating Changes (Planning)

When adding features:

1. Search existing specs: `openspec list --specs`
2. Create proposal: `openspec/changes/<change-id>/`
   - `proposal.md` - Why, what, impact
   - `tasks.md` - Implementation checklist
   - `design.md` - Technical decisions (if complex)
   - `specs/<capability>/spec.md` - Requirements with scenarios
3. Validate: `openspec validate <change-id> --strict`
4. Get approval before implementing

#### Stage 2: Implementing Changes (Building)

1. Read proposal.md
2. Follow tasks.md sequentially
3. Mark tasks complete immediately: `- [x]`
4. Run tests and validation

#### Stage 3: Archiving Changes (Cleanup)

After deployment:

```bash
openspec archive <change-id>
```

This moves the change to `changes/archive/` and updates `specs/`.

### Key Commands

```bash
openspec list                        # Show active changes
openspec list --specs                # Show deployed specs
openspec show <change-id>            # View change details
openspec diff <change-id>            # See spec changes
openspec validate <change-id>        # Validate
openspec archive <change-id>         # Archive after implementation
```

## 🔍 Understanding the Mathematical Model

The AUCS 2.0 model is defined by **39 equations (E1-E39)** in `docs/Urban_Amenities_Model_Spec.sty`:

### Core Equations

- **E1:** Generalized Travel Cost (GTC) - converts travel times to perceived costs
- **E2-E4:** Mode utilities and nested logsum - behavioral mode choice
- **E5:** Time-weighted accessibility w_{i,a}
- **E6-E9:** Destination quality Q_a with deduplication
- **E10-E13:** CES aggregation, satiation, diversity within categories
- **E14-E36:** Seven subscore computations
- **E37-E39:** Normalization and final AUCS aggregation

### Parameter Specification

600+ parameters controlling the model are specified in YAML format (see `docs/Urban_Amenities_Model_Spec.sty` section 3).

## 🚦 Implementation Priorities

### Critical Path (Must be sequential)

1. Core infrastructure
2. Data ingestion
3. Routing engines
4. Travel time computation
5. Amenity quality
6. Category aggregation
7. Subscores (can parallelize after step 6)
8. Score aggregation

### Can Be Parallelized

- Individual subscores after accessibility core is complete
- State-specific data ingestion (CO/UT/ID)
- Different routing profiles (car/bike/foot)

## 📖 Additional Resources

### In This Repository

- **Mathematical Spec:** `docs/Urban_Amenities_Model_Spec.sty`
- **Data Mapping:** `docs/urban_amenity_data_source_mapping`
- **API Mapping:** `docs/Urban Amenities API to parameter mapping.md`
- **Category Crosswalk:** `docs/AUCS place category crosswalk`

### External Documentation

- **H3:** <https://h3geo.org/>
- **Overture Maps:** <https://docs.overturemaps.org/>
- **GTFS Specification:** <https://gtfs.org/>
- **OpenTripPlanner:** <https://docs.opentripplanner.org/>
- **OSRM:** <http://project-osrm.org/>

## 🤝 Contributing

This project follows OpenSpec-driven development:

1. **Before coding:** Create or review change proposals in `openspec/changes/`
2. **During coding:** Follow tasks.md, mark tasks complete
3. **After coding:** Validate, test, then archive the change

## 📞 Getting Help

1. **OpenSpec workflow unclear?** → Read `openspec/AGENTS.md`
2. **Implementation approach unclear?** → Read `openspec/IMPLEMENTATION_GUIDE.md`
3. **Mathematical model unclear?** → Read `docs/Urban_Amenities_Model_Spec.sty`
4. **Data sources unclear?** → Read `docs/urban_amenity_data_source_mapping`
5. **Specific change unclear?** → Read the change's `proposal.md` and specs

## 📈 Project Timeline Estimate

- **Phase 1 (Foundation):** 3 weeks
- **Phase 2 (Accessibility Core):** 2 weeks
- **Phase 3 (Subscores):** 5 weeks (with parallelization)
- **Phase 4 (Output & QA):** 1 week
- **Phase 5 (Visualization):** 1-2 weeks

**Total: ~12 weeks** for a full implementation with a small team

---

**Ready to start?** → Open `openspec/IMPLEMENTATION_GUIDE.md` and begin with `add-core-infrastructure`! 🚀
