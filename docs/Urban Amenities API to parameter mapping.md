Absolutely—here’s a rigorous **API-to-parameter mapping** for the AUCS model (Aker Urban Convenience Score), aligned to the 250 m hex grid design and focused on Colorado, Utah, and Idaho. I’ve kept this strictly to **APIs, endpoints, required fields, transformations, and exactly which AUCS parameters they populate**. (We’ll wire in auth, caching, and job orchestration in the implementation doc.)

---

## Legend (what you’ll see below)

* **Param IDs** refer to the variables/equations in the AUCS spec you approved (e.g., `W_i`, `A_{i,m}`, `MORR_{i,transit}`, `Q_a`, `Diversity_i`, `σ_out`, etc.).
* **Hexes** = 250 m cells (e.g., H3 res=8). All transforms end in per-hex metrics.
* **Modes** `m` = walk, bike, car (drive), transit (and optionals: micromobility).
* **Quality Flags** = explicit filters to increase robustness.
* **ETL** notes assume bulk pulls + nightly deltas unless otherwise stated.

---

## 1) Places (amenities) & networks

### 1.1 Overture Maps — **Places & Transportation** (primary POI & network source)

**Access patterns**

* Bulk download via **S3/Azure URLs** or **BigQuery public dataset** (managed by CARTO). The BigQuery mirror is excellent for serverless querying by bbox/H3. ([Overture Maps Documentation][1])
* Transportation theme (segments/connectors) for routing graph prep; includes classes, restrictions, and speed rules. ([Overture Maps Documentation][2])

**Core files**

* **Places**: `theme=places` (GeoParquet), fields include identifiers, names, categories/classifiers, website/contact, brands, opening hours (see schema guide). ([Overture Maps Documentation][3])
* **Transportation**: `type=segment`, `type=connector` with attributes like class/surface/speed/access. ([Overture Maps Documentation][2])

**Maps to AUCS parameters**

* `S_a` (supply count per amenity class in each hex): spatial join of Places → 250 m hex; dedupe by place `id` + geometry; resolve confusions via `brand` and `classifiers`.
* `Q_a` (amenity quality proxy):

  * chain/brand recognition (brand field) → brand priors; opening_hours completeness; website presence; name entropy (proxy for uniqueness).
* `Diversity_i` (amenity diversity per hex): Shannon or Simpson index across AUCS categories aggregated in hex.
* Walk network reach (`A_{i,walk}`) baseline: length/connectivity from Transportation segments (class ∈ local roads, paths; surface/access filters).
* Drive/bike network prep (for OSRM): segment classes, speeds, access restrictions.

**Quality & frequency**

* Full refresh with Overture releases; BigQuery labels include release version; S3 path is date-versioned. ([Overture Maps Documentation][4])

**Notes**

* Overture is our **canonical place & road layer**; we only fall back to Overpass/OSM for niche tags not yet normalized in Overture.

---

### 1.2 Overpass API (OSM) — **gap filler for niche tags**

**Endpoint**: `https://overpass-api.de/api/interpreter` with Overpass QL; outputs JSON/GeoJSON/CSV. ([OpenStreetMap][5])

**Maps to AUCS**

* Specific amenity classes that Overture may under-cover locally (e.g., water fountains, trailheads with special tags): increment `S_a` & `Diversity_i` after de-duplication against Overture.
* Use strict bbox/timeouts and throttle; stage results to parquet with provenance.

---

## 2) Travel time, reachability & reliability

### 2.1 OSRM — **car/bike/walk travel-time & matrices**

**Hosted/own instance**; API routes include:

* `GET /route/v1/{profile}/{lon,lat;...}?overview=false&annotations=duration,distance`
* `GET /table/v1/{profile}/{coords}` for **many-to-many matrices** (durations/distances). ([Project OSRM][6])

**Profiles**: `car`, `bike`, `foot` built from Overture transportation graph (preprocessed with `osrm-extract`/`osrm-contract`).

**Maps to AUCS**

* `T_{i→p,m}` travel time from origin hex `i` to POI `p` (for `m ∈ {walk,bike,car}`) feeding:

  * **Accessibility kernel** `A_{i,m}` = Σ over POIs of decay `K(t)` (your chosen gravity/exponential kernel) to compute modality-specific access.
  * **Composite reach** `Reach_{i}` combining modes with your mode weights `w_m`.
* Congestion-insensitive (free-flow) baseline; optional peak factors can be added later.

**Quality**

* Reject candidates with snap distance > threshold (from `/nearest`). ([Project OSRM][7])

---

### 2.2 OpenTripPlanner 2.x — **transit trip plans & isochrones**

**Note**: OTP2 removed its legacy REST trip planner; use **GraphQL** (Transmodel/GTFS GraphQL sandbox APIs) for official queries. ([OpenTripPlanner][8])

**Endpoints** (self-hosted OTP2):

* GraphQL (Transmodel): `POST /otp/routers/default/transmodel/index/graphql` (trip plans, stops, departures). ([OpenTripPlanner][9])

**Inputs**

* Static GTFS: feeds for CO, UT, ID (via operator URLs or via **Transitland** discovery—see §2.3). ([GTFS][10])

**Maps to AUCS**

* `T_{i→p,transit}` transit itineraries (walk access + in-vehicle + transfer penalties) → **Transit accessibility** `A_{i,transit}` via same decay kernel `K(t)`.
* Optional `Isochrone_{i,transit,τ}` (OTP sandbox/analyst alternatives) to accelerate area-wise aggregation.

**Quality**

* Ensure router config for walk/bike speeds, max transfers, max walk. ([opentripplanner.readthedocs.io][11])

---

### 2.3 Transitland v2 — **Feed discovery, static GTFS and GTFS-RT helper**

**Purpose**: one **API** to discover & retrieve GTFS/GTFS-RT for CO/UT/ID and beyond (and GBFS, see §3).
**Base**: `https://transit.land/api/v2/rest` with API key. ([Transitland][12])

**Key endpoints**

* `GET /feeds?search={text}|bbox=...|spec=gtfs|gtfs-rt|gbfs` → returns static and RT URLs + license flags.
* `GET /feeds/{feed_key}/download_latest_feed_version` → GTFS zip (if license permits).
* `GET /feeds/{feed_key}/download_latest_rt/{alerts|trip_updates|vehicle_positions}.{json|pb}` → snapshot of GTFS-RT. ([Transitland][13])

**Maps to AUCS**

* **Data discovery** registry feeding OTP builds & RT monitors for **Colorado, Utah, Idaho**.
* **Reliability ingestion** (GTFS-RT JSON proxy) to compute `MORR_{i,transit}` KPIs (see §2.4).
* **GBFS** discovery for micromobility (see §3). ([Transitland][14])

---

### 2.4 GTFS Schedule & Realtime — **service, headways, on-time, span**

**Specs**

* GTFS Schedule reference (tables: routes, trips, stop_times, calendar, frequencies). ([GTFS][10])
* GTFS-RT (TripUpdates, VehiclePositions, Alerts). ([GTFS][15])

**Maps to AUCS** (per operator and per hex)

* **Frequency/Span** (`C3 Service Span`, `C4 Off-peak`) from static GTFS (stop departures per time-of-day & day-type).
* **Headway Reliability** (`C2`) from RT headways vs scheduled headways (`headway_deviation` distribution).
* **Punctuality/On-time** (`C1`) from TripUpdates: `delay` at timepoints; late/cancelled shares.
* **Alerts exposure** from Alerts feed (disruptions weighted by affected stops/routes/time).

**Realtime API examples (state coverage)**
Use Transitland to locate feeds. For illustration of **Utah/Colorado**:

* **UTA** (Utah Transit Authority) provides GTFS + RT; discovery docs on UTA developer site. ([Ride UTA][16])
* **RTD Denver** has developer resources for GTFS/RT; discoverable via Transitland. ([RTD Denver][17])
* **High Valley Transit** and **Park City** feeds visible in Transitland with feed URLs & versions (Park City GTFS: `go.parkcity.org/.../gtfs-zip.ashx`). ([Transitland][18])
* **Valley Regional Transit (Boise)** & **Pueblo Transit** (CO) RT also discoverable via Transitland. ([Pueblo][19])

> We’ll wire all agencies in CO/UT/ID by querying `/feeds?search={state name}|bbox=...` and persisting the registry; for each we record static URLs and RT endpoints and ingest on cadence. ([Transitland][13])

**Transforms → AUCS**

* `MORR_{i,transit}` = composite of `C1` punctuality, `C2` headway reliability, `C3` service span coverage, `C4` off-peak accessibility (weights as in your spec). Output at hex by demand-weighted aggregation over stops within walk thresholds (e.g., 800 m) and route importance.

---

## 3) Micromobility (GBFS)

**Spec & files**

* `gbfs.json` (auto-discovery), `system_information.json`, `station_information.json`, `station_status.json`, `free_bike_status.json` (etc.). ([General Bikeshare Feed Specification][20])

**Discovery**

* Via Transitland `spec=gbfs` in `/feeds` (aggregates many systems; fetched every 5 min). ([Transitland][14])

**Maps to AUCS**

* **First/last-mile factor** `C5 Micromobility availability` (option in `MORR` and in mode-mix accessibility): station density by hex, active docks/vehicles, operating hours.
* For CO/UT/ID, we rely on Transitland GBFS discovery + direct operator links as found.

---

## 4) Parks, trails, public lands & recreation

### 4.1 PAD-US (USGS) — **authoritative public lands/open space**

**Access**

* **Web services (ArcGIS FeatureServer/Views)** and **geodatabase downloads** (national/state). ([USGS][21])

**Maps to AUCS**

* `OpenSpace_i` (hectares within/adjacent to hex), public access flags, GAP status.
* `Trail proximity` when combined with USFS/NPS/Overture trails to enrich outdoor amenity supply.

### 4.2 USFS EDW, Trails & Recreation layers

* USFS enterprise data web services and national datasets (ArcGIS Map/Feature Services) for trails, rec sites. ([USDA Data][22])

### 4.3 NPS API & RIDB (Recreation.gov)

* **NPS API** (parks, visitor centers, events, alerts) requires API key. ([National Park Service][23])
* **RIDB** API (campgrounds, facilities, recreation areas). ([Recreation.gov][24])

**Maps to AUCS**

* Outdoor amenity classes (trails, parks, campgrounds, national parks) → `S_a`, `Diversity_i` and **Attraction Quality** `Q_a` (national park premium), plus **Popularity weight** via Wikipedia (below).

---

## 5) Popularity & cultural gravity (Wikimedia/Wikidata)

### 5.1 Wikimedia REST **pageviews**

* Endpoint (per article):
  `/metrics/pageviews/per-article/{project}/{access}/{agent}/{article}/{granularity}/{start}/{end}`. ([Wikimedia][25])

**Maps to AUCS**

* `Popularity_a` for attractions matched to their Wikipedia pages (via Wikidata id). Use rolling 12‑mo median or 95th percentile to reduce volatility; z-score within category. Boosts `Q_a` and long-range transit/drive kernels (e.g., NYC day-trip example).

### 5.2 Wikidata SPARQL & Action API

* **SPARQL** endpoint for entity reconciliation & geo/branding metadata: `https://query.wikidata.org/sparql`. ([MediaWiki][26])
* **wbgetentities** to resolve QIDs/labels/aliases. ([MediaWiki][27])

**Maps to AUCS**

* Disambiguation and metadata enrichment (type, inception, UNESCO status, etc.) → `Q_a` priors by attraction class.

---

## 6) Climate comfort & air quality

### 6.1 NOAA NCEI — **Climate Normals (1991–2020)**

* **Access Data Service**: `.../access/services/data/v1?dataset=normals-monthly-1991-2020&stations=...` (also daily/GSOM/LS). ([NCEI][28])
* Product pages (normals): references & docs. ([NCEI][29])

**Maps to AUCS**

* `σ_out` (seasonal outdoor comfort penalty) per hex via nearest-station or PRISM grid mapping—derive **“pleasant days”** index (bounds on `Tmean`, precip, snowfall) by month → weight outdoor amenity utility seasonally.

### 6.2 Air Quality (EPA AirNow / AQS)

* **AirNow** API (current/historical AQI by bbox/latlon/time). ([AirNow API Documentation][30])
* **AQS** API for monitor-level historical (row-level) data. ([AQS][31])

**Maps to AUCS**

* `AQ_penalty_i` = long-run average fraction of days ≥ AQI category thresholds → small dampening on **outdoor and active travel** utility terms.

---

## 7) Airports & intercity access

**FAA Enplanements** (annual, Excel/PDF; official) to rank/regress **gateway gravity** by airport size; then combine with **drive/transit time** from hex to airport (OSRM/OTP) to compute `GatewayAccess_i`. ([FAA][32])

*(Optional)* Use BTS/FAA APIs or data portals for supplemental air stats if needed. ([FAA API][33])

---

## 8) Demographic denominators (for per‑capita, equity overlays)

**U.S. Census API (ACS 5‑year)**

* Base endpoints (e.g., `.../data/2023/acs/acs5?get=NAME,B01003_001E&for=tract:*&in=state:08`), variable dictionary & guides. ([Census.gov][34])

**Maps to AUCS**

* Population/HH counts to normalize amenity supply or to stratify accessibility equity (not part of the score unless you include an equity modifier).

---

## 9) Childcare (market-specific add-on, since you asked earlier)

* **Colorado** licensed childcare locations — ArcGIS Feature Layer (JSON/GeoJSON enabled). **Direct ArcGIS REST** for query/export. ([CoHealth Maps][35])
* **Utah** & **Idaho**: public portals exist but **no stable open geocoded API** found; we’ll either use state open-data if published, or authoritative partner extracts. (We can still locate programs via Overture “childcare” category + manual curation.) ([Licensing & Background Checks][36])

**Maps to AUCS**

* Childcare as a core amenity class → `S_a`, `Q_a` (license type, capacity where available), `A_{i,m}` via travel times.

---

# Parameter-by-Parameter Mapping (concise crosswalk)

> **All outputs are per 250 m hex** unless noted. “Ops” = how to compute from the API data.

### A) Supply & Quality

| AUCS Param              | API / Dataset                                             | Endpoint / File                            | Fields used → Ops                                                                                       | Notes                                              |
| ----------------------- | --------------------------------------------------------- | ------------------------------------------ | ------------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| `S_a(i)` amenity counts | **Overture Places**                                       | S3/Azure/BigQuery tables                   | `classifiers`, `brand`, `name`, geometry → spatial join to hex; dedupe; filter by AUCS category mapping | Canonical POIs. ([Overture Maps Documentation][3]) |
| `Q_a` amenity quality   | **Overture Places**, **Wikidata/Wikipedia**, **NPS/RIDB** | (as above) + SPARQL + pageviews + NPS/RIDB | Brand premium; opening_hours presence; website; `Popularity_a` (pageviews), NPS unit boosts             | Class-specific scoring. ([Wikimedia][25])          |
| `Diversity_i`           | Overture Places                                           | (as above)                                 | Category proportions → Shannon/Simpson index per hex                                                    |                                                    |

### B) Travel-time Reachability (by mode)

| Param             | Mode    | API      | Endpoint                            | Fields → Ops                              |                        |
| ----------------- | ------- | -------- | ----------------------------------- | ----------------------------------------- | ---------------------- |
| `T_{i→p,walk}`    | Walk    | **OSRM** | `/table`, `/route` (`profile=foot`) | Durations, snapping QA                    | ([Project OSRM][6])    |
| `T_{i→p,bike}`    | Bike    | **OSRM** | `/table`, `/route` (`profile=bike`) | As above                                  |                        |
| `T_{i→p,car}`     | Drive   | **OSRM** | `/table`, `/route` (`profile=car`)  | As above                                  |                        |
| `T_{i→p,transit}` | Transit | **OTP2** | GraphQL Transmodel trip planning    | In-vehicle time, access/egress, transfers | ([OpenTripPlanner][9]) |
| `A_{i,m}`         | All     | Derived  | Gravity/decay kernel over `T`       | Your `K(t; α,β,…)`                        |                        |

### C) Transit Reliability (MORR)

| KPI               | API                          | Endpoint                         | Fields → Ops                                                           |                     |
| ----------------- | ---------------------------- | -------------------------------- | ---------------------------------------------------------------------- | ------------------- |
| `C1` On-time      | **GTFS-RT TripUpdates**      | `trip_update`                    | `delay`, `schedule_relationship`; compare to GTFS scheduled timepoints | ([GTFS][15])        |
| `C2` Headway rel. | **GTFS-RT VehiclePositions** | `vehicle.position`, `timestamp`  | Inter-arrival vs scheduled headways                                    |                     |
| `C3` Span         | **GTFS Schedule**            | `stop_times`, `calendar`         | Service hours coverage by route/stop/day-type                          | ([GTFS][10])        |
| `C4` Off-peak     | **GTFS Schedule**            | `stop_times` in off-peak windows | Off-peak minimum headway / availability                                |                     |
| Aggregation       | **Transitland v2**           | `/feeds`, `download_latest_rt/*` | Agency discovery; RT fetch helper (json/pb)                            | ([Transitland][13]) |

### D) Micromobility

| Param                | API             | Endpoint                                                      | Fields → Ops                               |                                              |
| -------------------- | --------------- | ------------------------------------------------------------- | ------------------------------------------ | -------------------------------------------- |
| `C5` First/last-mile | **GBFS**        | `system_information`, `station_information`, `station_status` | Stations/vehicles near hex; uptime; counts | ([General Bikeshare Feed Specification][20]) |
| Discovery            | **Transitland** | `/feeds?spec=gbfs`                                            | GBFS auto-discovery feeds                  | ([Transitland][14])                          |

### E) Outdoor Access & Comfort

| Param           | API           | Endpoint                                                            | Fields → Ops                                       |                                  |
| --------------- | ------------- | ------------------------------------------------------------------- | -------------------------------------------------- | -------------------------------- |
| `OpenSpace_i`   | **PAD‑US**    | ArcGIS services/FGDB                                                | Public-access polygons area intersecting hex       | ([USGS][21])                     |
| `σ_out` climate | **NOAA NCEI** | `.../access/services/data/v1?dataset=normals-monthly-1991-2020&...` | Monthly normals → “pleasant days” seasonal weights | ([NCEI][28])                     |
| `AQ_penalty_i`  | **AirNow**    | `.../webservices`                                                   | Daily AQI distributions mapped to hex → penalty    | ([AirNow API Documentation][37]) |

### F) Long-range Urban Access (e.g., NYC day-trip effect)

| Param             | API                                 | Endpoint                                  | Fields → Ops                                     |                   |
| ----------------- | ----------------------------------- | ----------------------------------------- | ------------------------------------------------ | ----------------- |
| `GatewayAccess_i` | **FAA enplanements** + **OSRM/OTP** | FAA XLSX; OSRM/OTP travel time to airport | Enplanements as hub weight × time-decay from hex | ([FAA][32])       |
| `Popularity_a`    | **Wikimedia**                       | Pageviews REST                            | Per-attraction pageviews → long-range interest   | ([Wikimedia][25]) |

### G) Denominators / Equity (optional in score)

| Param  | API            | Endpoint                         | Fields → Ops                          |                    |
| ------ | -------------- | -------------------------------- | ------------------------------------- | ------------------ |
| Pop/HH | **Census ACS** | `.../data/20YY/acs/acs5?get=...` | `B01003_001E` etc., hex interpolation | ([Census.gov][34]) |

---

## Transit coverage notes for CO • UT • ID (via API discovery)

* Use **Transitland /feeds** to enumerate all GTFS/RT feeds per state or within a state bbox; for each feed we cache `static_current`, `realtime_trip_updates`, `realtime_vehicle_positions`, `realtime_alerts` and license metadata (critical for redistribution). ([Transitland][13])
* Examples already verified in the catalog:

  * **Utah**: UTA developer data (static/RT available); **High Valley Transit**; **Park City** (`gtfs-zip.ashx`), all discoverable. ([Ride UTA][16])
  * **Colorado**: RTD developer feed; others (Transfort, Mountain Metro, Pueblo, RFTA, etc.) cataloged; we can programmatically list with `/feeds?search=Colorado`. ([RTD Denver][17])
  * **Idaho**: **Valley Regional Transit** (Boise) present in Transitland; use same pipeline. ([Pueblo][19])

*(We’ll store a **state agency registry** table from Transitland responses to drive OTP builds and RT monitoring.)*

---

## Example request patterns (for engineering handoff)

**OSRM travel-time matrix** (bike):

```
GET /table/v1/bike/{lon1},{lat1};{lon2},{lat2};...?
    annotations=duration&fallback_speed=...&sources=all&destinations=all
```

→ `durations[i][j]` → `T_{i→p,bike}`; quality: drop rows with `null`/huge snap distances. ([Project OSRM][6])

**OTP2 GraphQL (Transmodel)** trip plan (transit):

```
POST /otp/routers/default/transmodel/index/graphql
{ plan(fromPlace:{lat lon}, toPlace:{lat lon}, dateTime:..., modes:[WALK, TRANSIT], maxTransfers:2, walkSpeed:1.3 ) { itineraries { walkTime transitTime waitingTime generalizedCost } } }
```

Aggregate min/median itinerary time per OD bin to build `T_{i→p,transit}`; ensure walk parameters align with AUCS defaults. ([OpenTripPlanner][9])

**Transitland** RT snapshot (for reliability ops):

```
GET /api/v2/rest/feeds/{feed_key}/download_latest_rt/trip_updates.json?apikey=...
GET /api/v2/rest/feeds/{feed_key}/download_latest_rt/vehicle_positions.json?apikey=...
```

Parse JSON (Transitland decodes protobuf) → headway/OTD metrics. ([Transitland][13])

**Wikimedia pageviews** (popularity):

```
GET /metrics/pageviews/per-article/en.wikipedia/all-access/user/Arches_National_Park/daily/20240101/20241231
```

Compute rolling medians / z-scores per class. ([Wikimedia][25])

**NOAA normals** (monthly climate):

```
GET .../access/services/data/v1?dataset=normals-monthly-1991-2020&stations={ID}&startDate=0001-01-01&endDate=9999-12-31&format=json
```

Transform to **pleasant-day** weights per month; spatially map to hex. ([NCEI][28])

**PAD‑US** (ArcGIS Feature Layer):

```
GET {FeatureServer}/query?where=1=1&outFields=...&geometry={bbox}&outSR=4326&f=geojson
```

Intersect with hexes → accessible hectares. ([USGS][21])

**GBFS** (dock status):

```
GET {gbfs_url}/station_information.json
GET {gbfs_url}/station_status.json
```

Merge → live capacity/availability by hex. ([General Bikeshare Feed Specification][20])

---

## Implementation notes that affect parameter usability

1. **Licensing & redistribution**
   Transitland returns license flags (commercial use, derived products, redistribution). We honor these flags in pipeline outputs & caches. ([Transitland][13])

2. **OTP2 API change**
   OTP’s classic REST `/plan` is deprecated/removed—**GraphQL** is the supported path. Our router will expose the Transmodel GraphQL endpoint. ([OpenTripPlanner][8])

3. **Micromobility variability**
   GBFS coverage varies by city. Use Transitland GBFS discovery; where absent, we can integrate operator-specific GBFS roots if available locally. ([Transitland][14])

4. **Childcare**
   Colorado has a **live ArcGIS Feature Layer**; Utah/Idaho lack an official open geocoded API; for those we’ll rely on Overture POIs + state portals/manual exports where permissible. ([CoHealth Maps][35])

5. **Air quality**
   AirNow requires API key; we’ll compute a **multi‑year AQI distribution** per county/metro and downscale to hex by proximity to monitors. ([AirNow API Documentation][37])

---

## Putting it together (dataflow → parameters)

1. **Ingest registry** (Transitland feeds for CO/UT/ID) → static GTFS (for OTP graph) + RT endpoints list. ([Transitland][13])
2. **Build routing**:

   * OSRM per profile from Overture transport segments. ([Overture Maps Documentation][2])
   * OTP2 graph from GTFS + Overture walk/bike graph (or OSM if preferred for pedestrian detail). ([OpenTripPlanner][38])
3. **POIs**: Overture Places → AUCS categories → per-hex supply `S_a`, diversity. ([Overture Maps Documentation][3])
4. **Travel-times**: matrices from hex-centroids to POIs per mode (`OSRM`) and transit itineraries (`OTP2`).
5. **MORR**: Stream GTFS-RT snapshots; compute reliability KPIs and aggregate to hex via nearby stops & route weights. ([GTFS][15])
6. **Outdoors**: PAD‑US intersect; NOAA normals → `σ_out`; AirNow → `AQ_penalty_i`. ([USGS][21])
7. **Popularity**: Wikipedia pageviews + Wikidata linkage → `Popularity_a` → feed into `Q_a` and long-range gravity. ([Wikimedia][25])
8. **Airports**: FAA enplanements + OSRM/OTP to airports → `GatewayAccess_i`. ([FAA][32])

---

## Where this materially improves AUCS vs. “walkability-only”

* **Modal reach** is explicit and tunable: each mode contributes by **how much it unlocks** (decayed by travel time).
* **Reliability** is not hand-waved: `MORR` ties **live GTFS-RT** to the convenience score. ([GTFS][15])
* **Destination quality & gravity** are grounded in **open popularity signals** (Wikimedia) and **authoritative POI classes** (NPS, RIDB, PAD‑US, Overture). ([Wikimedia][25])
* **Regional gateways** matter (the NYC day-trip example), backed by FAA traffic scales and travel-time decays. ([FAA][32])

---

### Quick checklist (engineering)

* [ ] Provision **Overture** (BigQuery & S3) readers. ([Overture Maps Documentation][4])
* [ ] Build **OSRM** (car/bike/foot) from Overture transport; expose `/route` and `/table`. ([Project OSRM][6])
* [ ] Stand up **OTP2** with Transmodel GraphQL; schedule GTFS rebuilds from **Transitland** registry. ([OpenTripPlanner][9])
* [ ] Ingest **GTFS-RT** via Transitland JSON snapshots; compute MORR nightly + rolling windows. ([Transitland][13])
* [ ] Ingest **GBFS** where present; compute micromobility availability. ([Transitland][14])
* [ ] **PAD‑US** and **USFS/NPS/RIDB** enrich outdoor amenity classes. ([USGS][21])
* [ ] **Wikimedia** pageviews + **Wikidata** SPARQL for attraction popularity/metadata. ([Wikimedia][25])
* [ ] **NOAA NCEI** normals + **AirNow** AQI for environmental modifiers. ([NCEI][28])
* [ ] **FAA** enplanements for gateway gravity. ([FAA][32])
* [ ] **ACS** API for denominators/equity overlays. ([Census.gov][34])

---

If you’d like, I can now produce a **machine-readable mapping file** (YAML/JSON) that lists each **AUCS variable → API endpoint(s)** with **field selectors, transforms, and refresh cadence**—ready for ingestion orchestration.

[1]: https://docs.overturemaps.org/getting-data/?utm_source=chatgpt.com "Accessing the Data | Overture Maps Documentation"
[2]: https://docs.overturemaps.org/guides/transportation/?utm_source=chatgpt.com "Transportation | Overture Maps Documentation"
[3]: https://docs.overturemaps.org/guides/places/?utm_source=chatgpt.com "Places | Overture Maps Documentation"
[4]: https://docs.overturemaps.org/getting-data/data-mirrors/bigquery/?utm_source=chatgpt.com "BigQuery | Overture Maps Documentation"
[5]: https://wiki.openstreetmap.org/wiki/Overpass_API?utm_source=chatgpt.com "Overpass API - OpenStreetMap Wiki"
[6]: https://project-osrm.org/docs/v5.24.0/api/?utm_source=chatgpt.com "OSRM API Documentation"
[7]: https://project-osrm.org/docs/v5.7.0/api/?utm_source=chatgpt.com "OSRM API Documentation"
[8]: https://docs.opentripplanner.org/en/latest/apis/Apis/?utm_source=chatgpt.com "APIs"
[9]: https://docs.opentripplanner.org/en/v2.3.0/sandbox/TransmodelApi/?utm_source=chatgpt.com "Transmodel(NeTEx) GraphQL API"
[10]: https://gtfs.org/documentation/schedule/reference/?utm_source=chatgpt.com "General Transit Feed Specification Reference"
[11]: https://opentripplanner.readthedocs.io/en/latest/RouterConfiguration/?utm_source=chatgpt.com "Router configuration - OpenTripPlanner 2 - Read the Docs"
[12]: https://www.transit.land/documentation/rest-api/ "Transitland • Documentation • Transitland v2 REST API"
[13]: https://www.transit.land/documentation/rest-api/feeds "Transitland • Documentation • REST API - Feeds"
[14]: https://www.transit.land/documentation/concepts/source-feeds?utm_source=chatgpt.com "Documentation • Source Feeds"
[15]: https://gtfs.org/documentation/realtime/reference/?utm_source=chatgpt.com "GTFS Realtime Reference"
[16]: https://www.rideuta.com/data?utm_source=chatgpt.com "UTA Open Data Portal"
[17]: https://www.rtd-denver.com/open-records/open-spatial-information/gtfs?utm_source=chatgpt.com "GTFS"
[18]: https://www.transit.land/feeds/f-high~valley~transit~district?utm_source=chatgpt.com "GTFS feed details: f-high~valley~transit~district"
[19]: https://www.pueblo.us/3027/GTFS-Schedule-Dataset?utm_source=chatgpt.com "GTFS Schedule Dataset | Pueblo, CO - Official Website"
[20]: https://gbfs.org/?utm_source=chatgpt.com "General Bikeshare Feed Specification: Home"
[21]: https://www.usgs.gov/programs/gap-analysis-project/science/pad-us-web-services?utm_source=chatgpt.com "PAD-US Web Services | U.S. Geological Survey"
[22]: https://data.fs.usda.gov/geodata/edw/datasets.php?utm_source=chatgpt.com "Download National Datasets"
[23]: https://www.nps.gov/subjects/developer?utm_source=chatgpt.com "Developer Resources (U.S. National Park Service)"
[24]: https://ridb.recreation.gov/docs?utm_source=chatgpt.com "RIDB API"
[25]: https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/reference/page-views.html?utm_source=chatgpt.com "Page view analytics | Wikimedia Analytics API"
[26]: https://www.mediawiki.org/wiki/Wikidata_Query_Service/User_Manual?utm_source=chatgpt.com "Wikidata Query Service/User Manual"
[27]: https://www.mediawiki.org/wiki/Wikibase/API?utm_source=chatgpt.com "Wikibase/API"
[28]: https://www.ncei.noaa.gov/support/access-data-service-api-user-documentation?utm_source=chatgpt.com "NCEI Data Service API User Documentation"
[29]: https://www.ncei.noaa.gov/access/search/data-search/normals-monthly-1991-2020?utm_source=chatgpt.com "US Monthly Climate Normals (1991-2020)"
[30]: https://docs.airnowapi.org/?utm_source=chatgpt.com "AirNow API Documentation"
[31]: https://aqs.epa.gov/aqsweb/documents/data_api.html?utm_source=chatgpt.com "Air Quality System (AQS) API"
[32]: https://www.faa.gov/airports/planning_capacity/passenger_allcargo_stats/passenger/cy23_all_enplanements?utm_source=chatgpt.com "CY 2023 Enplanements at All Airports (Primary, Non- ..."
[33]: https://api.faa.gov/s/?utm_source=chatgpt.com "FAA API Portal - Federal Aviation Administration"
[34]: https://www.census.gov/data/developers/data-sets/acs-5year.html?utm_source=chatgpt.com "American Community Survey 5-Year Data (2009-2023)"
[35]: https://www.cohealthmaps.dphe.state.co.us/arcgis/rest/services/OPEN_DATA/cdphe_cdec_colorado_licensed_childcare_providers/MapServer/0?utm_source=chatgpt.com "Layer: CDPHE CDEC Licensed Childcare Providers (ID: 0)"
[36]: https://dlbc.utah.gov/home/office-of-licensing/child-care/?utm_source=chatgpt.com "Child care - Division of Licensing and Background Checks"
[37]: https://docs.airnowapi.org/webservices?utm_source=chatgpt.com "AirNow API - Web Services"
[38]: https://docs.opentripplanner.org/en/latest/Configuration/?utm_source=chatgpt.com "Introduction - OpenTripPlanner 2"
