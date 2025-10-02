# Interactive Visualization UI Implementation Tasks

## 1. UI Framework Setup (20 tasks)

### 1.1 Dash Application Scaffold

- [ ] 1.1.1 Install Dash and dependencies: `dash`, `plotly`, `dash-bootstrap-components`, `dash-leaflet`
- [ ] 1.1.2 Create `src/Urban_Amenities2/ui/app.py` with Dash app initialization
- [ ] 1.1.3 Configure Dash with Bootstrap theme (use `dbc.themes.BOOTSTRAP` or `FLATLY`)
- [ ] 1.1.4 Set up app layout structure: header, sidebar, main content, footer
- [ ] 1.1.5 Create `src/Urban_Amenities2/ui/layouts/` directory for page layouts
- [ ] 1.1.6 Implement multi-page routing (home, map view, data management, settings)
- [ ] 1.1.7 Create navigation sidebar with icons and links
- [ ] 1.1.8 Add application header with logo, title, and user info placeholder
- [ ] 1.1.9 Implement responsive layout (mobile, tablet, desktop breakpoints)
- [ ] 1.1.10 Set up custom CSS in `src/Urban_Amenities2/ui/assets/style.css`

### 1.2 Development Environment

- [ ] 1.2.1 Create `requirements-ui.txt` with all UI dependencies and versions
- [ ] 1.2.2 Set up hot-reload for development: `app.run_server(debug=True)`
- [ ] 1.2.3 Configure environment variables for UI (PORT, HOST, DEBUG, SECRET_KEY)
- [ ] 1.2.4 Create Docker Compose service for UI with volume mounting
- [ ] 1.2.5 Set up reverse proxy configuration (Nginx) for production
- [ ] 1.2.6 Implement health check endpoint: `/health` returns 200 OK
- [ ] 1.2.7 Configure CORS if API and UI on different domains
- [ ] 1.2.8 Set up logging for UI server (access logs, error logs)
- [ ] 1.2.9 Create development seed data (sample 1000 hexes for fast iteration)
- [ ] 1.2.10 Document local development setup in `docs/UI_DEVELOPMENT.md`

---

## 2. Data Loading and Management (20 tasks)

### 2.1 Parquet Data Loading

- [ ] 2.1.1 Create `src/Urban_Amenities2/ui/data_loader.py` module
- [ ] 2.1.2 Implement function to load AUCS Parquet files into pandas DataFrame
- [ ] 2.1.3 Add schema validation on load (verify required columns: hex_id, AUCS, EA, LCA, etc.)
- [ ] 2.1.4 Implement data versioning (track which run's outputs are currently loaded)
- [ ] 2.1.5 Add data refresh mechanism (reload files when new run completes)
- [ ] 2.1.6 Optimize loading with column selection (only load needed columns per view)
- [ ] 2.1.7 Implement data compression in memory (use categorical dtype for hex_id)
- [ ] 2.1.8 Add data filtering utilities (by state, metro, score range)
- [ ] 2.1.9 Create data summary statistics (min, max, mean, percentiles per subscore)
- [ ] 2.1.10 Implement data export functions (GeoJSON, CSV, Shapefile)

### 2.2 H3 Hex Geometry

- [ ] 2.2.1 Install h3-py for hex boundary computation
- [ ] 2.2.2 Create utility function: `hex_to_geojson(hex_id)` returns GeoJSON polygon
- [ ] 2.2.3 Batch convert all hex IDs to geometries on data load
- [ ] 2.2.4 Cache hex geometries (they never change for a given hex ID)
- [ ] 2.2.5 Create multi-resolution hex datasets (aggregate to H3 res 6, 7, 8 for zoom levels)
- [ ] 2.2.6 Implement spatial indexing (rtree or shapely STRtree) for viewport queries
- [ ] 2.2.7 Add function to query hexes in bounding box (lat/lon bounds)
- [ ] 2.2.8 Implement hex neighbor queries (for spatial autocorrelation viz)
- [ ] 2.2.9 Create hex centroid lookup (for label placement)
- [ ] 2.2.10 Validate hex coverage (check for gaps, overlaps)

---

## 3. Heat Map Visualization (25 tasks)

### 3.1 Choropleth Map Implementation

- [ ] 3.1.1 Create `src/Urban_Amenities2/ui/components/choropleth.py`
- [ ] 3.1.2 Implement `create_choropleth()` function using Plotly `go.Choroplethmapbox`
- [ ] 3.1.3 Configure mapbox access token (free tier sufficient for dev, paid for prod)
- [ ] 3.1.4 Set initial map center (center of CO/UT/ID region: ~39.5°N, -111°W)
- [ ] 3.1.5 Set initial zoom level (zoom=6 for 3-state view)
- [ ] 3.1.6 Define color scale for AUCS scores (0-100, sequential colormap: Viridis or RdYlGn)
- [ ] 3.1.7 Implement continuous color scale with legend
- [ ] 3.1.8 Add hover template showing: hex_id, score, lat/lon, metro area
- [ ] 3.1.9 Configure map style (streets, outdoors, satellite, or dark mode)
- [ ] 3.1.10 Enable zoom controls and fullscreen button

### 3.2 Multi-Scale Heat Map

- [ ] 3.2.1 Implement zoom level detection callback (track current zoom state)
- [ ] 3.2.2 Define zoom thresholds for resolution switching:
  - Zoom 0-5: H3 res 6 (large hexes, state-level)
  - Zoom 6-8: H3 res 7 (medium hexes, metro-level)
  - Zoom 9-11: H3 res 8 (small hexes, neighborhood-level)
  - Zoom 12+: H3 res 9 (finest hexes, block-level)
- [ ] 3.2.3 Pre-aggregate scores to coarser resolutions (mean or weighted average)
- [ ] 3.2.4 Implement automatic data switching based on zoom level
- [ ] 3.2.5 Add smooth transitions between zoom levels (fade in/out hexes)
- [ ] 3.2.6 Optimize by only rendering hexes in current viewport
- [ ] 3.2.7 Implement viewport-based data fetching (lazy load hexes as user pans)
- [ ] 3.2.8 Add loading spinner while fetching hex data for new viewport
- [ ] 3.2.9 Cache rendered layers per zoom level (avoid re-rendering)
- [ ] 3.2.10 Test performance with 10K, 100K, 1M hexes

### 3.3 Subscore Selection

- [ ] 3.3.1 Create dropdown component for subscore selection (Total AUCS, EA, LCA, MUHAA, JEA, MORR, CTE, SOU)
- [ ] 3.3.2 Implement callback to update choropleth when subscore changes
- [ ] 3.3.3 Adjust color scale per subscore (different scales if needed)
- [ ] 3.3.4 Update legend title to reflect current subscore
- [ ] 3.3.5 Display subscore description/tooltip (explain what EA, LCA, etc. measure)

---

## 4. Base Map and Geographic Context (20 tasks)

### 4.1 Base Map Layers

- [ ] 4.1.1 Integrate Mapbox base map styles (streets-v11, outdoors-v11, satellite-v9, dark-v10)
- [ ] 4.1.2 Create base map style selector (dropdown or radio buttons)
- [ ] 4.1.3 Ensure streets/roads visible at all zoom levels
- [ ] 4.1.4 Enable city labels (show major cities: Denver, Salt Lake City, Boise, etc.)
- [ ] 4.1.5 Add landmark labels (airports, universities, major parks)
- [ ] 4.1.6 Configure label collision detection (avoid overlapping labels)
- [ ] 4.1.7 Adjust label sizes based on zoom level (larger at higher zoom)
- [ ] 4.1.8 Test base map load times (ensure <2s initial load)
- [ ] 4.1.9 Implement fallback to OpenStreetMap if Mapbox unavailable
- [ ] 4.1.10 Add watermarks/attributions per map provider requirements

### 4.2 Geographic Overlays

- [ ] 4.2.1 Add state boundaries layer (CO, UT, ID outlines)
- [ ] 4.2.2 Add county boundaries layer (optional, toggle on/off)
- [ ] 4.2.3 Add metro area boundaries (Denver, SLC, Boise CBSAs)
- [ ] 4.2.4 Add transit lines layer (show GTFS routes from data)
- [ ] 4.2.5 Add transit stops layer (show GTFS stops, cluster at low zoom)
- [ ] 4.2.6 Add parks/trails layer (show PAD-US protected areas)
- [ ] 4.2.7 Create layer toggle panel (checkboxes to show/hide each layer)
- [ ] 4.2.8 Implement layer opacity sliders (adjust transparency)
- [ ] 4.2.9 Add layer ordering (heat map above base, but below labels)
- [ ] 4.2.10 Test layer combinations (ensure all layers render correctly together)

---

## 5. Interactive Controls and Filters (25 tasks)

### 5.1 Filter Panel

- [ ] 5.1.1 Create sidebar filter panel with collapsible sections
- [ ] 5.1.2 Add state filter (multi-select: CO, UT, ID)
- [ ] 5.1.3 Add metro area filter (multi-select: Denver, SLC, Boise, Colorado Springs, etc.)
- [ ] 5.1.4 Add county filter (searchable dropdown with all counties)
- [ ] 5.1.5 Add score range slider (min-max slider, 0-100)
- [ ] 5.1.6 Add population density filter (if hex-level data available)
- [ ] 5.1.7 Add land use filter (urban, suburban, rural categories)
- [ ] 5.1.8 Implement "Apply Filters" button (batch filter application for performance)
- [ ] 5.1.9 Add "Clear Filters" button (reset to default view)
- [ ] 5.1.10 Show filtered hex count (e.g., "Showing 5,432 of 1,000,000 hexes")

### 5.2 Parameter Adjustment

- [ ] 5.2.1 Create "Advanced Settings" panel (expandable section)
- [ ] 5.2.2 Expose subscore weights (7 sliders, constrain sum to 100)
- [ ] 5.2.3 Add decay parameter alpha sliders (per mode: walk, bike, transit, car)
- [ ] 5.2.4 Add value-of-time (VOT) inputs (weekday, weekend)
- [ ] 5.2.5 Add CES elasticity (rho) sliders per category
- [ ] 5.2.6 Add satiation kappa adjustments (per category)
- [ ] 5.2.7 Implement "Recalculate" button (trigger score recomputation with new params)
- [ ] 5.2.8 Show parameter diff indicator (highlight changed params)
- [ ] 5.2.9 Add "Reset to Defaults" button (restore original parameter values)
- [ ] 5.2.10 Display parameter validation errors (e.g., weights not summing to 100)

### 5.3 Hex Details and Drill-Down

- [ ] 5.3.1 Implement hex click callback (select hex, show details)
- [ ] 5.3.2 Create hex detail panel (show full score breakdown)
- [ ] 5.3.3 Display total AUCS and all 7 subscores for selected hex
- [ ] 5.3.4 Show top 5 contributing amenities (from explainability output)
- [ ] 5.3.5 Show top modes (walk, bike, transit, car accessibility)
- [ ] 5.3.6 Display hex metadata (lat/lon, metro area, county, population)
- [ ] 5.3.7 Add "Compare Hex" button (select multiple hexes for side-by-side comparison)
- [ ] 5.3.8 Implement hex highlighting (outline selected hex on map)
- [ ] 5.3.9 Add "Nearby Hexes" view (show neighboring hexes with scores)
- [ ] 5.3.10 Implement "Export Hex Data" button (download hex details as JSON/CSV)

---

## 6. Caching Layer Implementation (25 tasks)

### 6.1 Cache Architecture

- [ ] 6.1.1 Choose cache backend (DiskCache for simplicity, Redis for scalability)
- [ ] 6.1.2 Create `src/Urban_Amenities2/cache/manager.py` module
- [ ] 6.1.3 Implement `CacheManager` class with get/set/invalidate methods
- [ ] 6.1.4 Define cache key schema: `{source}:{entity_type}:{entity_id}:{timestamp}`
- [ ] 6.1.5 Set default TTL per data source:
  - Wikipedia pageviews: 24 hours
  - Wikidata entities: 7 days
  - NOAA climate: 30 days (static)
  - FAA airports: 90 days (annual updates)
  - Overture POIs: 90 days (quarterly updates)
  - GTFS feeds: 7 days (weekly updates)
- [ ] 6.1.6 Implement cache size limits (max 50GB, LRU eviction)
- [ ] 6.1.7 Add cache statistics tracking (hits, misses, evictions)
- [ ] 6.1.8 Create cache configuration file: `config/cache.yaml`
- [ ] 6.1.9 Implement cache warming (pre-populate common queries on startup)
- [ ] 6.1.10 Add cache compression (gzip or lz4 for large responses)

### 6.2 API Response Caching

- [ ] 6.2.1 Integrate cache into Wikipedia API client (`io/enrichment/wikipedia.py`)
- [ ] 6.2.2 Integrate cache into Wikidata API client (`io/enrichment/wikidata.py`)
- [ ] 6.2.3 Integrate cache into NOAA API client (`io/climate/noaa.py`)
- [ ] 6.2.4 Integrate cache into FAA data loader (`io/airports/faa.py`)
- [ ] 6.2.5 Integrate cache into Transitland API client (`io/gtfs/registry.py`)
- [ ] 6.2.6 Add cache headers to API responses (Last-Modified, ETag)
- [ ] 6.2.7 Implement conditional requests (If-Modified-Since, If-None-Match)
- [ ] 6.2.8 Handle cache misses gracefully (fetch from API, update cache)
- [ ] 6.2.9 Handle cache errors gracefully (fall back to API if cache unavailable)
- [ ] 6.2.10 Log all cache operations (hits, misses, updates, errors)

### 6.3 Routing Cache

- [ ] 6.3.1 Integrate cache into OSRM client (`router/osrm.py`)
- [ ] 6.3.2 Integrate cache into OTP2 client (`router/otp.py`)
- [ ] 6.3.3 Define routing cache key: `{profile}:{origin_hex}:{dest_hex}:{time_period}`
- [ ] 6.3.4 Set routing cache TTL: 30 days (graphs don't change often)
- [ ] 6.3.5 Implement cache invalidation on graph rebuild (delete all routing cache)
- [ ] 6.3.6 Pre-compute common OD pairs and cache proactively
- [ ] 6.3.7 Implement cache batch operations (get/set multiple keys at once)
- [ ] 6.3.8 Monitor routing cache hit rate (target >80%)
- [ ] 6.3.9 Add routing cache statistics to UI dashboard
- [ ] 6.3.10 Document routing cache key schema and TTL strategy

### 6.4 Cache Management UI

- [ ] 6.4.1 Create "Data Management" page in UI with cache dashboard
- [ ] 6.4.2 Display cache statistics: total size, hit rate, oldest entry, newest entry
- [ ] 6.4.3 Show cache status per data source (last updated, TTL remaining)
- [ ] 6.4.4 Add "Refresh" button per data source (manual cache invalidation)
- [ ] 6.4.5 Add "Refresh All" button (invalidate entire cache, fetch fresh data)
- [ ] 6.4.6 Implement progress indicators for refresh operations (show fetching status)
- [ ] 6.4.7 Add cache size visualization (pie chart showing size per source)
- [ ] 6.4.8 Add cache hit rate time series chart (track over time)
- [ ] 6.4.9 Implement "Clear Cache" button (delete all cached data)
- [ ] 6.4.10 Add confirmation dialog for destructive operations (clear cache, refresh all)

---

## 7. CLI Integration (20 tasks)

### 7.1 Job Submission Interface

- [ ] 7.1.1 Create "Pipeline" page in UI for running CLI commands
- [ ] 7.1.2 Add form for data ingestion: file upload or URL input
- [ ] 7.1.3 Add form for score computation: parameter file selection, region selection
- [ ] 7.1.4 Add form for data export: format selection (Parquet, GeoJSON, CSV), output path
- [ ] 7.1.5 Implement job submission endpoint: POST `/api/jobs`
- [ ] 7.1.6 Generate unique job IDs (UUID) for each submission
- [ ] 7.1.7 Store job metadata (command, parameters, status, timestamps)
- [ ] 7.1.8 Execute CLI commands as subprocess (use `subprocess.Popen`)
- [ ] 7.1.9 Capture stdout/stderr from CLI commands
- [ ] 7.1.10 Implement job cancellation (terminate subprocess on user request)

### 7.2 Job Status and Progress

- [ ] 7.2.1 Implement job status endpoint: GET `/api/jobs/{job_id}`
- [ ] 7.2.2 Track job states: pending, running, completed, failed, cancelled
- [ ] 7.2.3 Parse CLI log output for progress indicators (e.g., "Processing 50/100 hexes")
- [ ] 7.2.4 Display progress bar in UI (0-100% based on parsed logs)
- [ ] 7.2.5 Show estimated time remaining (based on current throughput)
- [ ] 7.2.6 Implement job list view (show all jobs: active, recent, historical)
- [ ] 7.2.7 Add job filtering (by status, date, command type)
- [ ] 7.2.8 Implement job log viewer (real-time streaming of stdout/stderr)
- [ ] 7.2.9 Add job result viewer (show outputs, download links)
- [ ] 7.2.10 Implement job notification (toast message when job completes)

---

## 8. Comparison and Analysis Tools (20 tasks)

### 8.1 Side-by-Side Comparison

- [ ] 8.1.1 Create "Compare" page with dual map view
- [ ] 8.1.2 Implement split-screen layout (left map, right map)
- [ ] 8.1.3 Add comparison mode selector:
  - Compare two runs (different parameter sets)
  - Compare two regions (e.g., Denver vs SLC)
  - Compare two subscores (e.g., EA vs LCA)
  - Compare before/after (time series)
- [ ] 8.1.4 Synchronize map zoom and pan between left/right views
- [ ] 8.1.5 Implement difference heat map (show delta between two runs)
- [ ] 8.1.6 Add scatter plot: X-axis = run 1 scores, Y-axis = run 2 scores
- [ ] 8.1.7 Compute correlation coefficient (R²) for comparison
- [ ] 8.1.8 Highlight hexes with largest differences (outliers)
- [ ] 8.1.9 Add summary statistics table (mean, median, std for each run)
- [ ] 8.1.10 Export comparison report (PDF or HTML with charts)

### 8.2 Time Series Visualization

- [ ] 8.2.1 Implement run history tracking (store metadata for all completed runs)
- [ ] 8.2.2 Create time series page showing AUCS trends over time
- [ ] 8.2.3 Add line chart: X-axis = run date, Y-axis = mean AUCS per metro
- [ ] 8.2.4 Implement animated heat map (play through runs chronologically)
- [ ] 8.2.5 Add animation controls (play, pause, speed, scrubber)
- [ ] 8.2.6 Show parameter changes over time (if params varied between runs)
- [ ] 8.2.7 Detect significant changes (alert if mean score changes >5%)
- [ ] 8.2.8 Add annotation support (attach notes to specific runs)
- [ ] 8.2.9 Export time series data (CSV with run metadata and scores)
- [ ] 8.2.10 Implement time series forecasting (if sufficient runs, predict future trends)

---

## 9. Export and Sharing (15 tasks)

### 9.1 Map Export

- [ ] 9.1.1 Implement "Export Map" button (download current view as image)
- [ ] 9.1.2 Support export formats: PNG, PDF, SVG
- [ ] 9.1.3 Add export options: resolution (DPI), include legend, include scale bar
- [ ] 9.1.4 Implement high-resolution export (2x, 4x pixel density)
- [ ] 9.1.5 Add watermark/attribution to exported maps
- [ ] 9.1.6 Export current viewport or full region (user choice)
- [ ] 9.1.7 Implement map export to interactive HTML (Plotly standalone HTML)
- [ ] 9.1.8 Test export file sizes (ensure <10MB per export)

### 9.2 Data Export

- [ ] 9.2.1 Implement "Export Data" button (download filtered hexes)
- [ ] 9.2.2 Support export formats: GeoJSON, CSV, Shapefile, GeoPackage
- [ ] 9.2.3 Include all columns or user-selected columns (column picker)
- [ ] 9.2.4 Apply current filters to export (only export visible hexes)
- [ ] 9.2.5 Add export progress indicator for large datasets
- [ ] 9.2.6 Implement streaming export (avoid loading all data in memory)
- [ ] 9.2.7 Test export with 1M hexes (ensure completes in <5 minutes)

---

## 10. Performance Optimization (20 tasks)

### 10.1 Front-End Optimization

- [ ] 10.1.1 Implement data decimation (reduce hex count for low zoom levels)
- [ ] 10.1.2 Use WebGL rendering for choropleth (Plotly `scattermapbox` with WebGL)
- [ ] 10.1.3 Implement viewport culling (only render hexes in view)
- [ ] 10.1.4 Lazy load hex geometries (fetch on zoom/pan)
- [ ] 10.1.5 Debounce zoom/pan events (reduce callback frequency)
- [ ] 10.1.6 Optimize callback chains (minimize Dash callback overhead)
- [ ] 10.1.7 Use client-side caching (store hex geometries in browser)
- [ ] 10.1.8 Implement progressive rendering (render coarse first, refine later)
- [ ] 10.1.9 Profile front-end performance with Chrome DevTools (target <100ms callback)
- [ ] 10.1.10 Test with slow network (3G throttling, ensure usable)

### 10.2 Back-End Optimization

- [ ] 10.2.1 Implement server-side hex aggregation (reduce data sent to browser)
- [ ] 10.2.2 Use Polars or DuckDB for fast DataFrame operations
- [ ] 10.2.3 Pre-compute common queries (cache aggregated data)
- [ ] 10.2.4 Implement spatial indexing (rtree for bounding box queries)
- [ ] 10.2.5 Use async callbacks where possible (non-blocking I/O)
- [ ] 10.2.6 Optimize Parquet loading (only load needed columns, partitions)
- [ ] 10.2.7 Implement background tasks (use Celery or RQ for long-running jobs)
- [ ] 10.2.8 Profile back-end with cProfile (identify bottlenecks)
- [ ] 10.2.9 Load test with 10 concurrent users (measure response times)
- [ ] 10.2.10 Optimize memory usage (target <4GB for UI server)

---

## 11. Deployment (20 tasks)

### 11.1 Production Build

- [ ] 11.1.1 Create production Dockerfile for UI (`Dockerfile.ui`)
- [ ] 11.1.2 Use multi-stage build (build assets, run server)
- [ ] 11.1.3 Pin all UI dependencies (requirements-ui.txt with versions)
- [ ] 11.1.4 Configure Gunicorn or Uvicorn as WSGI server (multi-worker)
- [ ] 11.1.5 Set worker count based on CPU cores (2 × cores + 1)
- [ ] 11.1.6 Configure worker timeout (300s for long-running callbacks)
- [ ] 11.1.7 Set up Nginx reverse proxy (serve static assets, proxy API calls)
- [ ] 11.1.8 Enable gzip compression for API responses (reduce bandwidth)
- [ ] 11.1.9 Set up HTTPS with Let's Encrypt (automatic SSL certificates)
- [ ] 11.1.10 Configure firewall rules (allow only 80/443, block direct app port)

### 11.2 Deployment Automation

- [ ] 11.2.1 Add UI service to Docker Compose (`docker-compose.yml`)
- [ ] 11.2.2 Configure environment variables for production (disable debug, set secret key)
- [ ] 11.2.3 Set up volume mounts (data, cache, logs)
- [ ] 11.2.4 Implement health check endpoint for UI service
- [ ] 11.2.5 Configure restart policy (always restart on failure)
- [ ] 11.2.6 Set resource limits (memory, CPU for UI container)
- [ ] 11.2.7 Add UI to CI/CD pipeline (build image on merge)
- [ ] 11.2.8 Deploy to staging environment first (test before production)
- [ ] 11.2.9 Implement blue-green deployment (zero-downtime updates)
- [ ] 11.2.10 Document deployment procedures in `docs/UI_DEPLOYMENT.md`

---

## 12. Security (15 tasks)

### 12.1 Authentication and Authorization

- [ ] 12.1.1 Implement user authentication (optional: basic auth, OAuth, SAML)
- [ ] 12.1.2 Hash passwords with bcrypt (if using basic auth)
- [ ] 12.1.3 Implement session management (secure cookies, CSRF protection)
- [ ] 12.1.4 Add role-based access control (viewer, analyst, admin roles)
- [ ] 12.1.5 Restrict sensitive operations to admin role (cache clear, job cancel)
- [ ] 12.1.6 Implement rate limiting (prevent abuse, max 100 req/min per user)
- [ ] 12.1.7 Add audit logging (track who did what, when)
- [ ] 12.1.8 Secure API endpoints (require auth token for all API calls)
- [ ] 12.1.9 Implement logout functionality (clear session, revoke token)
- [ ] 12.1.10 Test authentication bypass vulnerabilities

### 12.2 Input Validation and Security

- [ ] 12.2.1 Validate all user inputs (parameter values, filters, file uploads)
- [ ] 12.2.2 Sanitize inputs to prevent injection attacks (SQL, XSS)
- [ ] 12.2.3 Limit file upload sizes (max 100MB per upload)
- [ ] 12.2.4 Validate file types (only allow expected formats: CSV, Parquet, YAML)
- [ ] 12.2.5 Scan uploaded files for malware (use clamav or similar)

---

## 13. Testing (25 tasks)

### 13.1 Unit Tests

- [ ] 13.1.1 Test data loader functions (load Parquet, validate schema)
- [ ] 13.1.2 Test choropleth creation (verify output structure)
- [ ] 13.1.3 Test filter logic (state, metro, score range filters)
- [ ] 13.1.4 Test parameter validation (weight sum to 100, bounds checks)
- [ ] 13.1.5 Test cache manager (get, set, invalidate, TTL)
- [ ] 13.1.6 Test hex geometry conversion (H3 to GeoJSON)
- [ ] 13.1.7 Test spatial queries (bounding box, viewport culling)
- [ ] 13.1.8 Mock external dependencies (Parquet files, cache backend)
- [ ] 13.1.9 Achieve 80%+ coverage for UI modules
- [ ] 13.1.10 Run tests in CI/CD (on every push)

### 13.2 Integration Tests

- [ ] 13.2.1 Test full UI workflow: load data → filter → visualize → export
- [ ] 13.2.2 Test cache integration: hit, miss, refresh
- [ ] 13.2.3 Test CLI job submission: submit → track → complete
- [ ] 13.2.4 Test map interactions: zoom, pan, click, hover
- [ ] 13.2.5 Test comparison mode: load two runs, compute difference
- [ ] 13.2.6 Test export functions: PNG, PDF, GeoJSON
- [ ] 13.2.7 Test with real data (sample 10K hexes)
- [ ] 13.2.8 Test error scenarios (missing files, cache errors, API failures)
- [ ] 13.2.9 Test responsive design (mobile, tablet, desktop)
- [ ] 13.2.10 Run integration tests in staging environment

### 13.3 User Acceptance Testing

- [ ] 13.3.1 Conduct usability testing with 5-10 target users
- [ ] 13.3.2 Test typical workflows (explore region, adjust parameters, export)
- [ ] 13.3.3 Gather feedback on UI design and layout
- [ ] 13.3.4 Test accessibility (keyboard navigation, screen readers)
- [ ] 13.3.5 Iterate based on feedback (prioritize top 3 issues)

---

## 14. Documentation (15 tasks)

### 14.1 User Documentation

- [ ] 14.1.1 Create user guide: `docs/UI_USER_GUIDE.md`
- [ ] 14.1.2 Document map navigation (zoom, pan, layers)
- [ ] 14.1.3 Document filtering and parameter adjustment
- [ ] 14.1.4 Document hex detail view and drill-down
- [ ] 14.1.5 Document comparison mode and time series
- [ ] 14.1.6 Document export options (maps, data)
- [ ] 14.1.7 Create video tutorial (5-minute walkthrough)
- [ ] 14.1.8 Add tooltips and help text throughout UI
- [ ] 14.1.9 Create FAQ for common questions
- [ ] 14.1.10 Publish documentation website (MkDocs or similar)

### 14.2 Developer Documentation

- [ ] 14.2.1 Document UI architecture: `docs/UI_ARCHITECTURE.md`
- [ ] 14.2.2 Document caching strategy and TTL decisions
- [ ] 14.2.3 Document Dash callback structure and data flow
- [ ] 14.2.4 Document performance optimizations applied
- [ ] 14.2.5 Document deployment procedures and requirements

---

## 15. Polish and Launch (10 tasks)

### 15.1 Visual Design

- [ ] 15.1.1 Apply consistent color scheme (brand colors throughout UI)
- [ ] 15.1.2 Add AUCS logo and branding elements
- [ ] 15.1.3 Refine typography (consistent fonts, sizes, weights)
- [ ] 15.1.4 Add icons for all actions (FontAwesome or Material Icons)
- [ ] 15.1.5 Implement dark mode (toggle between light/dark themes)
- [ ] 15.1.6 Add loading animations and transitions (smooth UX)
- [ ] 15.1.7 Polish mobile layout (test on iOS and Android)
- [ ] 15.1.8 Review with designer (if available) for feedback
- [ ] 15.1.9 Conduct A/B testing on design variations (if applicable)
- [ ] 15.1.10 Final QA pass (fix all visual bugs, alignment issues)

---

**Total Tasks:** 290 across 15 workstreams
**Critical Path:** Framework setup → Data loading → Heat map → Caching → CLI integration → Testing → Deployment
**Estimated Timeline:** 4-6 weeks with dedicated UI/UX developer
