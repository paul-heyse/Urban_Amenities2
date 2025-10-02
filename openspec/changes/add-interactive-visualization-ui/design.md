# Interactive Visualization UI Design Document

## Context

AUCS 2.0 currently outputs data as Parquet files requiring technical expertise (Python, GIS software) to visualize and analyze. Stakeholders need an accessible, interactive interface to explore accessibility scores geographically, adjust parameters, and understand spatial patterns without coding.

**User Personas:**

1. **Urban Planners** - Need to identify low-accessibility neighborhoods, validate transit investments
2. **Real Estate Analysts** - Need to score locations for development, compare neighborhoods
3. **Policymakers** - Need to communicate findings, make data-driven decisions
4. **Researchers** - Need to conduct sensitivity analysis, validate model outputs
5. **General Public** - Need to understand their neighborhood's accessibility

**Key Requirements:**

- **Geographic heat maps** showing AUCS scores at multiple zoom levels
- **Interactive exploration** with filtering, drill-down, and comparison
- **Parameter experimentation** without writing code or rerunning entire pipeline
- **Performance** for 1M+ hexes (CO/UT/ID)
- **Intelligent caching** to avoid repeated expensive API calls

**Constraints:**

- Must integrate with existing AUCS CLI and data outputs (Parquet files)
- Must run on standard server (16GB RAM, 4-8 cores)
- Must support concurrent users (5-10 simultaneous)
- Must render smoothly on mobile, tablet, desktop

---

## Goals / Non-Goals

### Goals

1. **Beautiful, intuitive UI** that non-technical users can navigate
2. **Multi-scale heat maps** with smooth zoom from state to neighborhood level
3. **Real-time interactivity** with filters, parameter adjustments, hex drill-down
4. **Intelligent caching** of all external API calls (Wikipedia, Wikidata, etc.) with manual refresh
5. **CLI integration** to run pipeline jobs from UI
6. **Comparison tools** for multi-run analysis and sensitivity testing
7. **High performance** (<2s load time, <100ms interaction latency)

### Non-Goals

1. **Mobile app** (web-responsive is sufficient, not native iOS/Android)
2. **Real-time collaboration** (no simultaneous multi-user editing)
3. **Advanced GIS** (not replacing QGIS/ArcGIS, focused on AUCS-specific analysis)
4. **Routing interface** (not exposing OSRM/OTP2 directly, only AUCS results)
5. **Data ingestion UI** (heavy ETL still via CLI, UI for triggering only)

---

## Decisions

### Decision 1: Web Framework - Dash + Plotly

**What:** Use Plotly Dash as primary web framework with Plotly for visualizations.

**Why:**

- **Pure Python**: No JavaScript required, integrates seamlessly with existing AUCS codebase
- **Interactive visualizations**: Plotly excels at interactive charts and maps
- **Reactive callbacks**: Dash's callback system enables complex interactivity
- **Mature ecosystem**: Large community, extensive documentation, production-ready
- **Built-in components**: Dash Bootstrap Components for professional UI

**Alternatives considered:**

- **Streamlit**: Simpler but less flexible for complex layouts and state management
- **FastAPI + React**: More powerful but requires JavaScript expertise, slower development
- **Flask + Leaflet**: More work to build interactivity, less cohesive
- **Jupyter Dashboard**: Not production-ready, limited deployment options

**Implementation:**

- Dash 2.14+ with `dash-bootstrap-components` for layout
- Plotly 5.18+ for choropleths and charts
- `dash-leaflet` or custom Plotly `choroplethmapbox` for maps
- Gunicorn as WSGI server for production

**Trade-offs:**

- Pro: Fast development, Python-only, great for data apps
- Con: Less flexible than custom React, some performance limitations for very large datasets
- Mitigation: Use server-side aggregation and pagination for large datasets

---

### Decision 2: Map Visualization - Plotly Choroplethmapbox

**What:** Use Plotly's `go.Choroplethmapbox` for hex choropleth heat maps over Mapbox base maps.

**Why:**

- **Integrated**: Native Plotly component, works seamlessly with Dash
- **WebGL rendering**: Fast performance even with 100K+ hexes
- **Customizable**: Full control over colors, legends, hover tooltips
- **Base maps**: Supports Mapbox styles (streets, satellite, dark mode)
- **No external dependencies**: No need for separate Leaflet integration

**Alternatives considered:**

- **Dash-Leaflet**: Powerful but requires more JavaScript, harder to sync with Dash state
- **Pydeck**: Beautiful WebGL rendering but separate framework, harder to integrate
- **Folium**: Static maps, not truly interactive in Dash context
- **Kepler.gl**: Overkill for this use case, heavy front-end

**Implementation:**

- Define H3 hex GeoJSON for all hexes (compute once, cache)
- Create choropleth layer with score data (color scale by AUCS value)
- Mapbox base layer (requires Mapbox token: free tier OK for dev, paid for prod scale)
- Custom hover template: `{hex_id}<br>AUCS: {score:.1f}<br>Metro: {metro}`
- Zoom controls, fullscreen button, layer toggle

**Multi-scale strategy:**

- Pre-aggregate scores to H3 resolutions 6, 7, 8, 9
- Switch resolution based on zoom level:
  - Zoom 0-5: Res 6 (~100 hexes per state)
  - Zoom 6-8: Res 7 (~1000 hexes per metro)
  - Zoom 9-11: Res 8 (~10K hexes per county)
  - Zoom 12+: Res 9 (~1M hexes total)
- Reduces rendering load by 10-100× at low zoom

**Trade-offs:**

- Pro: Seamless integration, high performance, familiar to Plotly users
- Con: Requires Mapbox token (cost at scale), less GIS-native than Leaflet
- Mitigation: Document Mapbox token setup, provide OpenStreetMap fallback

---

### Decision 3: Caching Strategy - Multi-Tier with DiskCache

**What:** Implement three-tier caching: in-memory LRU, disk cache (DiskCache), and optional Redis for distributed deployments.

**Why:**

- **Performance**: External APIs (Wikipedia, Wikidata) are slow (100-500ms per call)
- **Cost**: Some APIs have rate limits or usage costs
- **Reliability**: Cache allows graceful degradation if APIs unavailable
- **User control**: Manual refresh ensures users see latest data when needed

**Cache Tiers:**

1. **In-Memory Cache** (LRU, 1GB max)
   - Hot data (frequently accessed hex geometries, base map tiles)
   - Lifetime: Process lifetime (cleared on restart)
   - Eviction: LRU when size limit reached

2. **Disk Cache** (DiskCache, 50GB max)
   - API responses (Wikipedia, Wikidata, NOAA, FAA, Transitland)
   - Routing results (OSRM/OTP2 travel times)
   - Lifetime: Per-source TTL (see below)
   - Eviction: LRU when size limit reached

3. **Redis Cache** (Optional, for multi-server)
   - Shared cache across UI server instances
   - Only if deploying with load balancer
   - Not required for single-server deployment

**TTL Strategy:**

| Data Source | TTL | Rationale |
|-------------|-----|-----------|
| Wikipedia pageviews | 24 hours | Daily metrics, changes daily |
| Wikidata entities | 7 days | Static facts, rarely change |
| NOAA climate | 30 days | 30-year normals, static |
| FAA airports | 90 days | Annual updates |
| Overture POIs | 90 days | Quarterly releases |
| GTFS feeds | 7 days | Weekly updates typical |
| OSRM routing | 30 days | Graph stable between updates |
| OTP2 routing | 7 days | Graph updated weekly |

**Cache Key Schema:**

```
{source}:{entity_type}:{entity_id}:{param_hash}
```

Examples:

- `wikipedia:pageviews:Q5107:2025-10-02`
- `osrm:table:car:hex1234_hex5678:peak`
- `wikidata:entity:Q5107`

**Manual Refresh UI:**

- "Data Management" page shows cache status per source
- "Last Updated" timestamp for each source
- "Refresh" button per source (invalidates cache, fetches fresh)
- "Refresh All" button (nuclear option, invalidates entire cache)
- Progress indicators during refresh (show fetching status)
- Toast notifications on completion

**Implementation:**

- `src/Urban_Amenities2/cache/manager.py` - Central cache manager class
- Integrate into all data loaders (wrapper functions with `@cache` decorator)
- Store cache metadata (timestamps, hit rates) in SQLite
- Background thread to clean expired entries daily

**Trade-offs:**

- Pro: Dramatic performance improvement, graceful API degradation, user control
- Con: Disk space usage (50GB), cache staleness risk, complexity
- Mitigation: Clear TTL communication, prominent refresh UI, disk space monitoring

---

### Decision 4: Data Loading - Lazy Loading with Viewport Queries

**What:** Load only hexes in current viewport + small buffer, fetch more as user pans/zooms.

**Why:**

- **Performance**: Cannot load 1M hexes into browser (>500MB, 30s+ load time)
- **Responsiveness**: User shouldn't wait for full data load to start exploring
- **Bandwidth**: Minimize data transfer, especially on mobile

**Implementation:**

1. **On initial load:**
   - Load metadata (bounding boxes, metro areas, score statistics)
   - Load viewport hexes for default view (3-state view, ~1000 hexes)
   - Display immediately

2. **On zoom/pan:**
   - Detect viewport change (Dash callback on map relayout)
   - Query backend for hexes in new viewport (bounding box query)
   - Use spatial index (rtree or Shapely STRtree) for fast lookup
   - Return GeoJSON with scores for visible hexes
   - Update choropleth layer

3. **Viewport buffer:**
   - Fetch hexes for 1.5× viewport size (0.5× buffer on each side)
   - Pre-fetch adjacent viewports (user likely to pan)
   - Cache fetched hexes in browser (avoid re-fetching on back-pan)

4. **Resolution switching:**
   - At low zoom (state-level), fetch coarse hexes (H3 res 6)
   - At high zoom (neighborhood), fetch fine hexes (H3 res 9)
   - Seamless transition: fade out coarse, fade in fine

**Backend API:**

```python
GET /api/hexes?bbox=west,south,east,north&resolution=9&subscore=AUCS
Response: GeoJSON FeatureCollection with ~500-5000 hexes
```

**Trade-offs:**

- Pro: Fast initial load, responsive interactions, scales to millions of hexes
- Con: More complex implementation, requires spatial indexing
- Mitigation: Pre-build spatial indices on data load, test with 1M hexes

---

### Decision 5: Parameter Adjustment - Client-Side Preview + Server-Side Recompute

**What:** Allow users to adjust key parameters in UI, show instant preview (linear approximation), then trigger full recomputation if desired.

**Why:**

- **Exploration**: Users want to see "what if" without waiting for full pipeline rerun
- **Education**: Interactive sliders help users understand parameter impacts
- **Validation**: Sensitivity analysis requires many parameter variations

**Two-Phase Approach:**

**Phase 1: Instant Preview (Client-Side)**

- User adjusts parameter (e.g., change EA weight from 30 to 35)
- **Linear rescaling** of scores in browser:

  ```python
  new_AUCS = (old_AUCS - old_EA * 30 + old_EA * 35) / 100
  ```

- Update choropleth immediately (<100ms)
- Show "Preview Mode" banner (scores are approximate)
- Limitations: Only accurate for weight changes, not decay/VOT changes

**Phase 2: Full Recomputation (Server-Side)**

- User clicks "Recalculate" button
- Submit job to backend: `POST /api/jobs/recompute` with new parameters
- Run score aggregation stage only (skip data ingestion, routing)
- Track progress, show spinner
- Auto-refresh map when complete (~5-30 min depending on scope)

**Exposed Parameters:**

*Simple (preview-capable):*

- Subscore weights (EA, LCA, MUHAA, JEA, MORR, CTE, SOU) - sum to 100
- Category weights within subscores

*Complex (require recomputation):*

- Decay alpha (per mode)
- Value of time (VOT)
- CES elasticity (rho)
- Satiation kappa

**UI Implementation:**

- Grouped slider panels (collapsible sections)
- Real-time validation (e.g., weights sum to 100)
- "Reset to Defaults" button
- Parameter diff viewer (highlight changes from baseline)
- Save custom parameter sets (presets)

**Trade-offs:**

- Pro: Instant feedback for simple changes, full accuracy when needed
- Con: Preview approximations may mislead users
- Mitigation: Clear "Preview Mode" indicators, documentation on limitations

---

### Decision 6: Hex Detail Drill-Down - Modal with Score Breakdown

**What:** On hex click, show modal popup with full score breakdown, top contributors, and metadata.

**Why:**

- **Understanding**: Users need to see *why* a hex has a specific score
- **Validation**: Spot-check model outputs for reasonableness
- **Storytelling**: Extract narratives from specific locations

**Modal Content:**

1. **Header:** Hex ID, lat/lon, metro area, county
2. **Score Summary:** Total AUCS (large, prominent) + all 7 subscores (bar chart)
3. **Top Contributors:**
   - Top 5 accessible amenities (from explainability output)
   - For each: name, category, distance, quality score
4. **Mode Breakdown:** Accessibility by mode (walk, bike, transit, car)
5. **Nearby Hexes:** Table of neighboring hexes with scores (for context)
6. **Actions:**
   - "Compare Hex" (add to comparison set)
   - "Export Hex Data" (JSON/CSV)
   - "View in Google Maps" (open lat/lon in Google Maps)

**Implementation:**

- Dash Bootstrap `Modal` component
- Triggered by hex click callback
- Fetch hex details from backend: `GET /api/hexes/{hex_id}/details`
- Cache details for recently clicked hexes (avoid repeated fetches)
- Responsive design (full-screen modal on mobile)

**Comparison Mode:**

- "Compare" button adds hex to comparison set (max 5 hexes)
- Comparison panel shows side-by-side: scores, contributors, maps
- Highlight differences (which hex has better EA, LCA, etc.)

**Trade-offs:**

- Pro: Rich detail, helps users understand scores
- Con: Requires explainability output (not in base AUCS), adds complexity
- Mitigation: Gracefully degrade if explainability unavailable (show scores only)

---

### Decision 7: CLI Integration - Job Queue with Background Workers

**What:** Run CLI commands as background jobs via Celery or Python `multiprocessing`, track status, stream logs.

**Why:**

- **Long-running**: Data refresh, recomputation take minutes to hours
- **Responsive**: UI should not block while job runs
- **Multi-user**: Multiple users should be able to submit jobs without interference

**Architecture:**

1. **Job Submission:**
   - User fills form (command, parameters)
   - UI sends `POST /api/jobs` with job spec
   - Backend generates job ID (UUID)
   - Backend spawns subprocess or Celery task
   - Returns job ID to UI immediately

2. **Job Execution:**
   - Execute CLI command: `aucs run --config custom.yaml --region CO`
   - Capture stdout/stderr
   - Parse logs for progress indicators
   - Update job status in database (pending → running → completed/failed)

3. **Job Monitoring:**
   - UI polls `GET /api/jobs/{job_id}/status` every 5 seconds
   - Display progress bar based on parsed logs
   - Stream logs to "Job Log" panel (real-time tail)
   - Show ETA based on current throughput

4. **Job Completion:**
   - On success: auto-reload visualization data, show toast notification
   - On failure: show error message, offer to view full logs
   - Store job results (output files, logs, metadata) for 30 days

**Job Types:**

- Data refresh (re-run ingestion for specific source)
- Score recomputation (with new parameters)
- Data export (to GeoJSON, Shapefile, etc.)
- Cache refresh (fetch latest from APIs)

**Technology Choice:**

*Option A: Celery (distributed, complex)*

- Pro: Scales to multiple workers, handles task queues
- Con: Requires Redis/RabbitMQ, adds deployment complexity

*Option B: Python multiprocessing (simple, sufficient)*

- Pro: No external dependencies, simpler deployment
- Con: Single-server only, less robust for many concurrent jobs

**Decision:** Start with **multiprocessing**, migrate to Celery if >10 concurrent users.

**Trade-offs:**

- Pro: Users can trigger pipeline from UI, track progress
- Con: Job management adds complexity, requires process management
- Mitigation: Clear job status UI, automatic cleanup of old jobs

---

### Decision 8: Comparison Mode - Side-by-Side Maps with Difference Layer

**What:** Split-screen map view comparing two runs/regions/subscores with synchronized zoom and difference choropleth.

**Why:**

- **Sensitivity analysis**: How does changing alpha affect scores?
- **Regional comparison**: Denver vs Salt Lake City
- **Temporal analysis**: Before/after infrastructure investment
- **Validation**: Compare with external benchmarks (Walk Score)

**UI Layout:**

- Two-column layout (50/50 split or adjustable divider)
- Each column: independent choropleth map with controls
- Synchronized zoom/pan (optional toggle)
- Third panel (below or side): difference heat map
- Summary statistics table: mean, median, std, correlation

**Difference Calculation:**

```python
difference = run2_score - run1_score
# Diverging color scale: red (run1 better), blue (run2 better)
```

**Comparison Modes:**

1. **Run-to-Run:** Compare two parameter sets
   - Load outputs from two runs
   - Show both maps + difference
   - Highlight parameters that changed

2. **Region-to-Region:** Compare two metros
   - Filter hexes to region 1 and region 2
   - Show side-by-side maps
   - Compute z-scores for fair comparison

3. **Subscore-to-Subscore:** EA vs LCA
   - Load same run, different subscores
   - Identify trade-offs (high EA, low LCA)

4. **Temporal:** Before/after
   - Load two runs from different dates
   - Animate transition between runs
   - Highlight hexes with large changes

**Statistical Outputs:**

- Correlation coefficient (R²)
- Mean absolute difference (MAD)
- % of hexes with >10-point change
- Scatter plot: X = run1, Y = run2 (diagonal line = perfect correlation)

**Trade-offs:**

- Pro: Powerful analysis tool, supports key use cases
- Con: Doubles data load, complex UI layout
- Mitigation: Lazy load both runs, responsive layout

---

### Decision 9: Export - High-Resolution Maps and Rich Data Formats

**What:** Export current map view as image (PNG, PDF) and filtered hex data as GeoJSON, Shapefile, or GeoPackage.

**Why:**

- **Reports**: Embed maps in presentations, reports, papers
- **GIS Integration**: Load AUCS data into QGIS, ArcGIS for further analysis
- **Sharing**: Send static maps to stakeholders without UI access

**Map Export:**

- Use Plotly's `fig.write_image()` for static export
- Formats: PNG, PDF, SVG
- Options:
  - Resolution (DPI): 72 (screen), 150 (print), 300 (high-res)
  - Size: current view or custom dimensions
  - Include legend, scale bar, attribution
- Add watermark/timestamp (optional)
- Export current view or full region (user choice)

**Data Export:**

- Formats: GeoJSON, CSV, Shapefile, GeoPackage
- Apply current filters (only export visible hexes)
- Column selection (all columns or user-specified)
- Coordinate system: WGS84 (EPSG:4326) default, option for State Plane
- Metadata file: include parameter hash, run date, filters applied

**Implementation:**

- "Export" button in toolbar
- Modal with export options (format, resolution, filters)
- Backend endpoint: `POST /api/export` returns download link
- Stream large exports (avoid loading all data in memory)
- Clean up temp export files after 1 hour

**Trade-offs:**

- Pro: Enables external workflows, professional outputs
- Con: Large exports (1M hexes = 500MB GeoJSON) can be slow
- Mitigation: Streaming export, file size warnings, recommend filtering

---

### Decision 10: Performance - Server-Side Aggregation and WebGL Rendering

**What:** Aggregate hex data on server before sending to browser, use WebGL for rendering.

**Why:**

- **Scale**: 1M hexes × 10 columns × 64 bytes = 640MB (too large for browser)
- **Latency**: Parsing 640MB JSON in browser takes 10+ seconds
- **Rendering**: SVG rendering of 1M polygons is prohibitively slow

**Server-Side Optimizations:**

1. **Spatial Aggregation:**
   - At low zoom: send H3 res 6 (100-1000 hexes)
   - At high zoom: send H3 res 9 (10K-100K hexes in viewport)
   - Never send >100K hexes at once

2. **Column Pruning:**
   - Only send columns needed for current view
   - Example: For choropleth, send: `[hex_id, score, geometry]`
   - Omit: explainability, metadata, other subscores

3. **Viewport Culling:**
   - Use spatial index (rtree) to query hexes in bounding box
   - Typical viewport: ~5,000 hexes at zoom 12
   - Query time: <50ms with proper indexing

4. **Caching:**
   - Cache aggregated data per zoom level
   - Avoid re-aggregating on every request

**Client-Side Optimizations:**

1. **WebGL Rendering:**
   - Use Plotly's `scattermapbox` with `mode='markers'` for hexes
   - Or use `choroplethmapbox` (native WebGL support)
   - Render 100K+ polygons at 60fps

2. **Debouncing:**
   - Debounce zoom/pan events (wait 200ms after user stops)
   - Avoid excessive callbacks during rapid interactions

3. **Progressive Rendering:**
   - Render coarse hexes immediately (placeholder)
   - Fetch and render fine hexes in background
   - Smooth transition

4. **Client Caching:**
   - Cache fetched hex data in browser (localStorage or IndexedDB)
   - Avoid re-fetching on back-navigation

**Performance Targets:**

- Initial load: <2 seconds
- Zoom/pan response: <500ms
- Filter update: <1 second
- Full data export: <5 minutes (1M hexes)

**Trade-offs:**

- Pro: Smooth performance at scale, responsive interactions
- Con: More complex backend, requires spatial indexing
- Mitigation: Profile and optimize, load testing with 1M hexes

---

## Architectural Patterns

### Hexagonal Architecture Integration

UI layer is an **adapter** in hexagonal architecture:

```
┌─────────────────────────────────────────────┐
│           UI (Dash Application)             │
│  ┌───────────────────────────────────────┐  │
│  │    Presentation Layer (Layouts)       │  │
│  └───────────────────────────────────────┘  │
│  ┌───────────────────────────────────────┐  │
│  │    Callbacks (User Interactions)      │  │
│  └───────────────────────────────────────┘  │
│  ┌───────────────────────────────────────┐  │
│  │    Data Adapters (Load Parquet)       │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│         Core AUCS Logic (Pure)              │
│  ┌───────────────────────────────────────┐  │
│  │  Score Computation, Math Kernels      │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│      Data Layer (I/O Adapters)              │
│  ┌───────────────────────────────────────┐  │
│  │  Parquet, Cache, Routing, APIs        │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

UI does NOT reimplement core logic. Instead:

- Loads pre-computed scores from Parquet
- For parameter changes: calls core scoring functions
- For data refresh: triggers CLI via subprocess

### Data Flow

```
User Action (Filter, Zoom, Click)
  │
  ▼
Dash Callback (Python function)
  │
  ▼
Data Adapter (Query Parquet or Cache)
  │
  ▼
Spatial Index / Aggregation
  │
  ▼
GeoJSON Response (500-5000 hexes)
  │
  ▼
Plotly Choropleth Update
  │
  ▼
Browser Render (WebGL)
```

---

## Risks / Trade-offs

### Risk 1: Performance with 1M Hexes

**Risk:** Rendering 1M hexes may be too slow even with optimizations.

**Mitigation:**

- Multi-resolution strategy (H3 res 6/7/8/9 based on zoom)
- Viewport culling (only render visible hexes)
- Server-side aggregation (don't send all data to browser)
- WebGL rendering (Plotly native support)
- Load testing: Verify <2s load time with 100K hexes
- Fallback: If still slow, limit to 50K hexes, require filtering for full detail

---

### Risk 2: Mapbox Token Costs

**Risk:** Mapbox charges per 1000 map loads; costs could escalate with many users.

**Mitigation:**

- Free tier: 50,000 map loads/month (sufficient for small deployments)
- Caching: Cache rendered map tiles in browser (reduce loads)
- OpenStreetMap fallback: Implement tile server for OSM (self-hosted, free)
- Pricing monitoring: Set alerts for usage approaching limits
- Cost-sharing: Pass costs to client if deployed for specific organization

---

### Risk 3: Cache Staleness

**Risk:** Users may see outdated data if cache not refreshed.

**Mitigation:**

- Prominent "Last Updated" timestamps in UI
- Automatic staleness warnings (if cache >30 days old)
- Easy manual refresh (single button per source)
- Documentation: Explain cache purpose and refresh process
- Default to short TTLs (7-30 days) for most sources

---

### Risk 4: Parameter Adjustment Misleading

**Risk:** Instant preview (linear rescaling) may mislead users about true parameter impacts.

**Mitigation:**

- Clear "Preview Mode" banner when using approximations
- Documentation on preview limitations
- "Recalculate" button prominently placed
- Compare preview vs full recomputation in validation testing
- Disable preview for complex parameter changes (decay, VOT)

---

### Risk 5: Concurrent Job Conflicts

**Risk:** Multiple users triggering jobs simultaneously may cause resource contention or data corruption.

**Mitigation:**

- Job queue with rate limiting (max 3 concurrent jobs)
- Job locking (prevent same job type running twice)
- Resource monitoring (alert if CPU/memory saturated)
- User notifications: "Queue position: 2" if jobs pending
- Graceful degradation: Disable job submission if system overloaded

---

## Migration Plan

### Phase 1: Core UI and Visualization (Weeks 1-2)

**Goal:** Basic heat map with filtering and zoom.

1. Set up Dash application scaffold
2. Implement Parquet data loader
3. Create choropleth heat map (single resolution)
4. Add state/metro filters
5. Implement hover tooltips
6. Test with 10K hexes (Boulder County)

**Success Criteria:**

- Map loads in <2 seconds
- Filters work without page reload
- Hover shows hex details

---

### Phase 2: Multi-Scale and Caching (Weeks 2-3)

**Goal:** Smooth multi-scale zoom and intelligent caching.

1. Pre-aggregate to H3 res 6, 7, 8
2. Implement zoom-based resolution switching
3. Build spatial index (rtree) for viewport queries
4. Implement cache manager (DiskCache)
5. Integrate cache into data loaders
6. Create cache management UI
7. Test with 100K hexes (metro-level)

**Success Criteria:**

- Zoom transitions smooth (<500ms)
- Cache hit rate >80%
- Manual refresh works

---

### Phase 3: Interactivity and Drill-Down (Weeks 3-4)

**Goal:** Hex details, comparison, and parameter adjustment.

1. Implement hex click modal with score breakdown
2. Add parameter adjustment panel with preview
3. Implement side-by-side comparison mode
4. Add export (maps and data)
5. Test with full 1M hexes (3 states)

**Success Criteria:**

- Hex details load <1 second
- Parameter preview instant (<100ms)
- Comparison mode shows difference heat map

---

### Phase 4: CLI Integration and Jobs (Weeks 4-5)

**Goal:** Run pipeline jobs from UI.

1. Implement job submission endpoint
2. Execute CLI commands as subprocesses
3. Track job status and progress
4. Stream logs to UI
5. Auto-refresh data on job completion
6. Test with real data refresh job

**Success Criteria:**

- Job submission works without blocking UI
- Progress bars accurate
- Data auto-updates after job completes

---

### Phase 5: Polish and Deployment (Week 5-6)

**Goal:** Production-ready UI with beautiful design.

1. Apply consistent styling (colors, fonts, layout)
2. Add dark mode
3. Optimize for mobile/tablet
4. Write user documentation
5. Create video tutorial
6. Deploy to production server
7. Load test with 10 concurrent users

**Success Criteria:**

- UI passes usability testing (5-10 users)
- All interactions <1s latency
- Documentation complete
- Deployed and accessible

---

## Open Questions

1. **Authentication:** Should UI require login? Basic auth, OAuth, or public?
   - **Decision needed by:** Week 4 (before deployment)
   - **Options:** Public (simplest), basic auth (moderate), OAuth (most secure)

2. **Multi-metro support:** Should UI support regions beyond CO/UT/ID?
   - **Decision needed by:** After Phase 5 (based on expansion plans)
   - **Impact:** May require region selector, dynamic data loading

3. **Mobile app:** Is a native mobile app needed, or is responsive web sufficient?
   - **Decision needed by:** After Phase 5 (based on user feedback)
   - **Trade-off:** Native app has better UX but 2-3× development time

4. **Collaboration features:** Should users be able to share custom parameter sets or annotate maps?
   - **Decision needed by:** After Phase 5 (based on user requests)
   - **Impact:** Requires user accounts, database for shared state

5. **API for external tools:** Should we expose a REST API for programmatic access?
   - **Decision needed by:** After Phase 5 (based on demand)
   - **Impact:** Requires API versioning, rate limiting, documentation

---

## Success Metrics

**Technical Metrics:**

- Load time: <2 seconds (initial map load)
- Interaction latency: <500ms (filter, zoom, pan)
- Cache hit rate: >80% (for API responses)
- Concurrent users: 5-10 without degradation
- Test coverage: 70%+ for UI modules

**User Metrics:**

- Usability score: >4/5 (from user testing)
- Adoption: >50% of stakeholders use UI (vs CLI/Parquet)
- Task completion: 90% of users can filter, zoom, export without help

**Business Metrics:**

- Reduced time-to-insight: From hours (download, code) to minutes (explore UI)
- Broader audience: Non-technical users can access AUCS insights
- Decision impact: UI-derived insights lead to planning/policy decisions

---

## Timeline

**Total Duration:** 4-6 weeks with dedicated UI developer

**Critical Path:**

1. Week 1-2: Core UI and visualization (blocks everything)
2. Week 2-3: Multi-scale and caching (required for performance)
3. Week 3-4: Interactivity (enhances usability)
4. Week 4-5: CLI integration (enables data refresh)
5. Week 5-6: Polish and deployment (production readiness)

**Parallelization:**

- Documentation can be written throughout (Weeks 1-6)
- Testing can start in Week 3 (alongside feature development)

**Buffer:** 1-2 weeks for unexpected issues, iteration based on user feedback
