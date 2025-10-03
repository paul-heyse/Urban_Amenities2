Below is a **comprehensive narrative overview** of the AUCS 2.0 model—how it works end‑to‑end on a 250 m hex grid—followed by a **practical, opinionated Python stack** that maps each part of the pipeline to specific libraries, with implementation notes and a ready‑to‑lift dependency set.

---

## 1) Narrative model overview (AUCS 2.0)

**Goal**
Quantify *what residents can reach* and *how easily they can reach it*—not only by walking, but also by transit, biking/micromobility, and driving—while weighting destinations by their **quality, diversity, novelty, and seasonal usability**, and factoring in the **reliability & resilience** of local mobility options.

**Spatial unit**
A regular lattice of **~250 m hex cells** (e.g., H3 r≈9). All inputs (POIs, stops, jobs, parks, airports) and outputs (subscores, final score) are computed **per hex**.

**Core idea**
For each hex (i), compute a time‑ and mode‑aware **accessibility weight** to each destination (a): a **nested logsum** over modes that converts generalized travel time (including wait/transfer penalties, reliability buffers, out‑of‑pocket costs) into a single reachability term (w_{i,a}). Multiply that by a **destination quality** (Q_a) (capacity, popularity, attributes), aggregate within categories using a **CES + satiation** curve (to avoid runaway returns from many similar places), then blend categories into interpretable **subscores**:

* **Essentials Access (EA)** – daily‑need categories
* **Leisure & Culture Access (LCA)** – restaurants/cafés/bars, museums/performing arts/cinemas, parks/trails, sports/rec, with diversity & novelty bonuses
* **Major Urban Hub & Airport Access (MUHAA)** – gravity of big city centers and airports, decayed by actual access time
* **Jobs & Education Access (JEA)** – jobs (LEHD LODES) and universities (IPEDS/Carnegie) reachable
* **Mobility Options, Reliability & Resilience (MORR)** – frequency, span, on‑time/headway stability, redundancy, micromobility
* **Corridor Trip‑Chaining (CTE)** – how easy it is to add errands along your common transit path(s) with minimal detour
* **Seasonal Outdoors Usability (SOU)** – climate‑weighted parks/trails convenience

Subscores map to 0–100 via metro‑relative percentiles (or absolute anchors), then AUCS is the **weighted sum** of subscores.

**Why it’s different**

* *Multi‑modal by construction* (not just walk scores).
* *Behavioral realism* via nested logsum and generalized cost.
* *Quality, variety, and novelty* of destinations explicitly modeled.
* *Reliability & redundancy* of mobility are first‑class.
* *Explainable:* each hex stores the top contributing amenities/modes/paths.

---

## 2) End‑to‑end dataflow (what you’ll build)

**A) Ingest & normalize**

* **Places & networks** (Overture Places/Transportation).
* **Transit schedules & realtime** (agency GTFS + GTFS-RT).
* **Micromobility** (GBFS).
* **Parks/open space** (PAD-US & trail sources).
* **Jobs & education** (LODES, NCES/IPEDS/Carnegie).
* **Airports** (FAA enplanements).
* **Climate** (NOAA normals) and optional **air quality**.
* **Typing note:** Ingestion clients expose typed interfaces (BigQuery fallbacks, HTTP params, GTFS realtime). When adding sources, prefer `Mapping`-based request payloads and provide optional dependency stubs so `mypy src/Urban_Amenities2/io --warn-unused-ignores` remains clean.

**B) Enrich & index**

* Apply **Overture→AUCS category crosswalk**; dedupe POIs (brand/name/distance).
* Attach Wikidata/Wikipedia to selected venues (for popularity/capacity).
* **Hex‑index** everything (H3) and keep raw Parquet tables partitioned by region.

**C) Routers**

* Build **OSRM** profiles for walk/bike/drive on the Overture network.
* Build **OTP2** graph (Overture walk/bike + all GTFS in market).

**D) Travel‑time matrices & logsums**

* Compute many‑to‑many **durations** from hexes to POIs/hubs/jobs/universities by mode & time‑slice.
* Construct **generalized travel cost** (add wait, transfers, reliability buffer, fare→minutes).
* Compute **mode utilities** → **nested logsum** → (w_{i,a}).

**E) Quality, diversity, novelty**

* Compute (Q_a) from venue attributes (capacity, popularity, tags/brand).
  * **Size & capacity** → log-scaled metric that blends square footage, seating, collection size, or Wikidata capacity with category medians filling gaps.
  * **Popularity** → combines Wikipedia median pageviews, sitelink counts, and observed z-scores, clipped per category to avoid single-outlier spikes.
  * **Brand recognition** → boosts well-known chains or Wikidata-branded venues while tempering unnamed independents.
  * **Heritage** → flags museums, libraries, and official heritage designations (e.g., UNESCO) as premium destinations.
* Normalize each component to 0–100 inside the category, then weight by (size=30 %, popularity=40 %, brand=15 %, heritage=15 %).
* Apply an opening-hours bonus (24/7 → +20 %, extended → +10 %, limited → −10 %) blended by `opening_hours_bonus_xi` to ensure late-night access matters without overwhelming other factors.
* Deduplicate chain saturation: same-brand POIs inside 500 m get an exponential penalty (`1 - exp(-β·d_km)`), and weights are rescaled so total category mass is preserved.
* Emit `quality_components`, `quality_hours_category`, `brand_penalty`, and `brand_weight` for explainability and downstream auditing.
* Automated validation: unit coverage in `tests/test_quality.py` and integration coverage via `tests/test_data_ingestion.py::test_enrichment_and_quality`.
* Aggregate (Q_a \cdot w_{i,a}) within categories via **CES + satiation**; add **within‑category diversity** bonus and **novelty** from pageview volatility.

**F) Subscores & AUCS**

* EA, LCA, MUHAA, JEA, MORR, CTE, SOU → **normalize** → **weighted sum**.
* Persist both **total AUCS** and **explainability artifacts** (top amenities, best modes, corridor baskets).

**G) Ops**

* **Incremental updates** (diffs for Overture/GTFS; rolling reliability windows).
* **QA** (coverage dashboards, invariants), **profiling** (performance & memory), and **tests** (unit/integration).

---

## 3) Python library stack (battle‑tested & mapped to tasks)

Below is an opinionated stack that balances performance, stability, and ecosystem maturity. Think of it as “what to `pip/poetry add` when you start coding.”

### 3.1 Core data, performance & geospatial

| Purpose           | Libraries                                     | Why / Notes                                                               |
| ----------------- | --------------------------------------------- | ------------------------------------------------------------------------- |
| Columnar core     | **pandas**, **numpy**, **pyarrow**            | Pandas for tabular; Arrow for zero‑copy Parquet/IPC.                      |
| Faster frames     | **polars** *optional*                         | Very fast lazy queries on Parquet; great for large POI tables.            |
| Embedded SQL      | **duckdb**                                    | Query Parquet *in place*, perfect for cross‑table joins and H3 group‑bys. |
| Geospatial vector | **geopandas**, **shapely>=2**, **pyproj**     | Vector ops; Shapely 2 brings speedups; CRS handling.                      |
| Spatial index     | **rtree**                                     | Fast nearest‑neighbor (dedupe & stop/POI snapping).                       |
| Hex grids         | **h3** (a.k.a. h3‑py), **h3ronpy** *optional* | Hex encode/aggregate; h3ronpy adds vectorized helpers.                    |
| Raster/climate    | **xarray**, **rioxarray**, **rasterio**       | Map NOAA gridded normals or AQ rasters to hexes.                          |
| Parallel          | **dask[dataframe]** or **ray**                | Parallelize big joins/isochrone aggregations.                             |
| Accel math        | **numba**                                     | JIT critical kernels (logsum, decay, saturation).                         |

### 3.2 Routing, GTFS & mobility

| Purpose           | Libraries                             | Why / Notes                                            |
| ----------------- | ------------------------------------- | ------------------------------------------------------ |
| GTFS (static)     | **partridge**, **gtfs‑kit**           | Fast readers; headway/stop‑time ops; validation.       |
| GTFS‑Realtime     | **gtfs‑realtime‑bindings** (protobuf) | Parse TripUpdates/VehiclePositions/Alerts.             |
| OTP2 GraphQL      | **gql** (GraphQL client), **httpx**   | Query trip plans/isochrones; async support with httpx. |
| OSRM HTTP         | **httpx** or **requests**             | Simple, robust access to `/route` and `/table`.        |
| GBFS              | **requests/httpx** (+ small helper)   | Station information/status polling.                    |
| Micromobility ops | **geopandas**, **pandas**             | Compute station densities, availability KPIs.          |

> Alternative router: **r5py** (R5 engine) can replace OTP if you prefer all‑Java routing without GraphQL. Keep one stack consistent across markets.

### 3.3 APIs & enrichment

| Purpose                | Libraries                                      | Why / Notes                                                |
| ---------------------- | ---------------------------------------------- | ---------------------------------------------------------- |
| Wikidata/Wikipedia     | **SPARQLWrapper**, **qwikidata**, **requests** | Resolve QIDs & page titles; pull pageviews.                |
| Wikimedia pageviews    | **requests/httpx**                             | Simple REST; compute rolling medians/IQR.                  |
| NOAA normals           | **requests**, **pandas**                       | Access Data Service endpoints; reshape to monthly scalars. |
| Air quality (optional) | **requests**, **pandas**                       | AirNow / AQS APIs for AQI distributions.                   |
| Cloud storage          | **fsspec**, **s3fs**, **adlfs**, **gcsfs**     | Read/write Parquet on S3/ADLS/GCS uniformly.               |
| BigQuery (Overture)    | **google‑cloud‑bigquery**, **pandas‑gbq**      | If you read Overture public tables in BQ.                  |

### 3.4 Engineering quality, config & orchestration

| Purpose              | Libraries                                            | Why / Notes                                           |
| -------------------- | ---------------------------------------------------- | ----------------------------------------------------- |
| Config & params      | **pydantic**, **pydantic‑settings**, **ruamel.yaml** | Strict, versioned parameter spec (the YAML you have). |
| Validation           | **pandera**                                          | Schema checks on all intermediate tables.             |
| Retries & rate limit | **tenacity**, **backoff**                            | Wrappers for flaky APIs.                              |
| Caching              | **diskcache**, **joblib**, **cachetools**            | Avoid recomputing big queries/matrices.               |
| Logging              | **structlog** or **loguru**                          | Structured logs; easier ops.                          |
| CLI                  | **typer**                                            | First‑class CLIs for each pipeline stage.             |
| Orchestration        | **prefect** or **apache‑airflow**                    | Scheduling, retries, observability.                   |
| Testing              | **pytest**, **hypothesis**                           | Unit + property tests for math kernels.               |
| Docs                 | **mkdocs‑material**                                  | Lightweight internal documentation site.              |

### 3.5 Visualization (dev & explainability)

| Purpose | Libraries                                                  | Why / Notes                                       |
| ------- | ---------------------------------------------------------- | ------------------------------------------------- |
| Maps    | **folium**, **pydeck**, **geopandas.plot**, **contextily** | Quick QA maps; hex choropleths; corridor visuals. |
| Charts  | **matplotlib**, **plotnine**, **altair**                   | Subscore distributions, calibration plots.        |

---

## 4) Implementation blueprint (how libraries wire into the math)

### 4.1 Parameters, config & reproducibility

* Define the **param spec YAML** (you already have) and load via **pydantic** models.
* Version every run (hash of param YAML + data snapshot IDs) and persist to a `runs/` table.
* Use **ruamel.yaml** for precise round‑tripping (so the config file is the contract).

### 4.2 Places & categories

* Read Overture Places (Parquet/BigQuery) with **pyarrow**/**duckdb**.
* Apply the **category crosswalk** (prefix matcher) with **pandas** or **polars**; store `aucstype`, `brand`, `confidence`.
* Deduplicate per hex using **rtree** nearest neighbors and **rapidfuzz** on `(name, brand)` with a small distance threshold.
* Output: `pois.parquet` (hex‑indexed).

### 4.3 Networks & routers

* Build **OSRM** extracts from Overture Transportation (preprocess externally; Python uses **requests/httpx** to call `/route` & `/table`).
* Build **OTP2** graph (CLI/JVM). From Python, use **gql/httpx** to hit the Transmodel GraphQL endpoint.
* Provide a **router client** module that normalizes outputs into a single schema:

  ```text
  origin_hex | dest_id | mode | period | duration_min | access_walk_min |
  ivt_min | wait_min | transfers | fare_usd | ok
  ```

### 4.4 Travel-time matrices & nested logsum

* Fetch **many‑to‑many matrices** (OSRM `/table`) for walk/bike/drive.
* Batch OTP2 **trip plans** by OD hex cluster to compute transit generalized times.
* Implement the generalized cost and nested logsum kernels in **numpy** (JIT with **numba**), ensuring:

  * Stable **log‑sum‑exp** trick to avoid overflow.
  * Vectors per mode/time slice for (\theta), (\delta), (\rho), and (\text{VOT}).
  * Return the final (w_{i,a} = \sum_\tau w_\tau \exp(W_{i,a,\tau})).

### 4.5 Amenity quality, diversity & novelty

* Compute (Q_a) by category:

  * Scale/clip z‑scores (capacity, size, popularity) with **numpy/scipy**.
  * **Wikidata/Wikipedia** enrichment using **SPARQLWrapper/qwikidata** and **requests** (pageviews).
  * Brand de‑duplication kernel (distance‑weighted) with **numpy**.

* Compute **within‑category diversity** (Shannon/Hill) for each hex using **numpy** on `Q`‑weighted shares.

### 4.6 Category CES & satiation

* Implement **CES** aggregator and **satiation** curve in a vectorized kernel; JIT with **numba** if needed.
* Use **pandera** checks to assert monotonicity and range.

### 4.7 Subscores

* **EA/LCA**: apply category rules; for LCA compute CES+satiation per leisure category (restaurants, cafes, bars, cinemas, performing arts, museums/galleries, parks/trails, sports/rec), apply Wikipedia novelty bonus, then cross-category CES using parameters from `params.leisure_cross_category`.
* **MUHAA**: build **hub mass** table (BEA/Census + POI + culture) weighted by `params.hubs_airports.hub_mass_weights`; decay by generalized travel cost using mode-best times; weight airports by enplanements × airport-specific multipliers and combine hub/airport access using configurable contributions.
* **JEA**: load LODES with **duckdb**, aggregate by hex, then gravity via (w_{i,\text{block}}) matrices.
* **MORR**: poll GTFS‑RT with **httpx** for on-time reliability (fallback to schedules when GTFS-RT missing); compute frequency/share of frequent stops, span coverage, redundancy, and micromobility density; aggregate with weights from `params.morr`.
* **CTE**: build top 2 paths using OTP2; buffer stops (Shapely), collect corridor POIs, compute small‑detour utility.
* **SOU**: compute a base parks/trails accessibility score by applying CES + satiation to weighted park quality (area, amenities, designation) using travel-time weights, then compute (\sigma_{\text{out}}) per time slice from **NOAA** monthly normals and multiply the parks score; log join timings and capture metrics for QA.

### 4.8 Normalization & AUCS

* Use metro‑relative percentiles (5th–95th) computed in **duckdb** to map raw subscores to 0–100.
* Compose **AUCS** with the weight vector from the params.
* Persist: `aucs.parquet` (hex → all subscores + AUCS + top contributors JSON).

### 4.9 Explainability

* Store per‑hex “**Top contributors**”: the top‑K ((Q_a \cdot w_{i,a})) amenities, best modes, and corridor baskets.
* Use **pydeck/folium** for QA maps; **matplotlib/altair** for distributions and calibration plots.

---

## 5) Practical dependency set (you can drop in)

> Python **3.11** recommended.

**Core**

* `numpy`, `pandas`, `pyarrow`, `duckdb`, `polars` (optional), `numba`

**Geo**

* `geopandas`, `shapely>=2.0`, `pyproj`, `rtree`, `h3` (and optionally `h3ronpy`), `rasterio`, `xarray`, `rioxarray`, `pyogrio`

**Routing & mobility**

* `requests`, `httpx`, `gql[requests]` (OTP GraphQL), `partridge`, `gtfs-kit`, `gtfs-realtime-bindings`

**APIs & enrichment**

* `SPARQLWrapper`, `qwikidata`, `pydantic`, `ruamel.yaml`, `pandas-gbq` (if pulling Overture from BigQuery), `google-cloud-bigquery` (optional), `fsspec`, `s3fs`, `adlfs`, `gcsfs`, `tenacity`, `backoff`, `rapidfuzz`, `unidecode`

**Quality, orchestration & ops**

* `pandera`, `typer`, `structlog` (or `loguru`), `prefect` (or `apache-airflow`), `diskcache`, `cachetools`, `joblib`, `pytest`, `hypothesis`, `mkdocs-material`, `tqdm`, `rich`

**Viz (optional but useful)**

* `matplotlib`, `altair`, `folium`, `pydeck`, `contextily`

---

## 6) Module/layout suggestion

```
aker-aucs/
  configs/
    params.yml              # your AUCS parameter spec (versioned)
    feeds_CO_UT_ID.yml      # GTFS/GBFS registries (state-scoped)
  data/                     # external data (parquet/arrow), partitioned by state/yyyymm
  src/
    au cs/config.py         # Pydantic models for params
    au cs/io/               # readers: overture, gtfs, gbfs, noaa, faa, wikidata
    au cs/xwalk/            # overture→AUCS category matcher
    au cs/hex/              # H3 utilities
    au cs/router/osrm.py    # OSRM client
    au cs/router/otp.py     # OTP GraphQL client
    au cs/gtfs/             # headways, span, validation (partridge/gtfs-kit)
    au cs/realtime/         # GTFS-RT polling & reliability KPIs
    au cs/quality/          # Q_a, popularity, dedupe kernels
    au cs/math/             # logsum, CES, satiation, diversity (numba)
    au cs/scores/           # EA, LCA, MUHAA, JEA, MORR, CTE, SOU
    au cs/norm/             # percentile/anchor normalization
    au cs/export/           # parquet writers; explainability JSON
  tests/
    unit/                   # math kernels, I/O contracts
    integration/            # mini-market smoke tests
  docs/
    index.md
```

---

## 7) Performance & reliability tips

* **Batch routing**: For OSRM `/table`, cluster OD pairs by proximity; for OTP, group ODs per time slice and reuse router instances.
* **Top‑K pruning**: For dense categories (restaurants), keep only **top‑K by `Q_a`** within 90 minutes to cap compute.
* **Vectorize**: Implement logsum, CES, satiation with **numpy** and **numba**; avoid Python loops.
* **Arrow everywhere**: Keep Parquet+Arrow as the interchange; use **duckdb** to avoid materializing huge joins in RAM.
* **Caching**: Cache API hits and matrices (**diskcache**) keyed by (origin‑tile, destination‑tile, mode, period, feed version).
* **Schema checks**: Use **pandera** on every table (e.g., ensure durations ≥ 0, route_type enums valid).
* **Idempotency**: Every stage should be rerunnable with the same inputs → same outputs (hash checks).

---

## 8) Validation & calibration

* **Face validity**: Hexes near frequent rail should get higher MUHAA/JEA even if local walk options are modest.
* **Elasticity checks**: Sensitivity runs for half‑lives, transfer penalties, and mode constants; visualize shifts with **altair**.
* **Ground truth**: Compare EA with survey data (e.g., % residents satisfied with local essentials) if available; check MORR against agency reliability reports.
* **Cross‑market consistency**: Percentile‑based normalization per metro plus a national “anchor view” to ensure fair comparisons across CO/UT/ID.

---

## 9) What you’ll have at the end

* `aucs.parquet` — hex‑level **AUCS** & all **subscores** (0–100)
* `explainability.parquet` — top contributors per hex (amenity, mode, time, contribution)
* `skims_*.parquet` — reusable travel‑time matrices by mode/time
* `feeds_registry.parquet` — GTFS/GBFS endpoints used and versions
* fully versioned **params.yml** + **run manifest**

This overview plus the library map is everything a team needs to start building. If you want, I can also provide a **starter `pyproject.toml`** with pinned major versions and a few bootstrap scripts (e.g., `make build-osrm`, `make build-otp`, `python -m aucs.scores.run --market=CO`).
