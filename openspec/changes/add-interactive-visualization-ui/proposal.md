# Interactive Visualization UI for AUCS 2.0

## Why

AUCS 2.0 currently outputs Parquet files and requires technical expertise to analyze. Stakeholders (urban planners, real estate analysts, policymakers) need:

1. **Visual exploration** - Heat maps showing accessibility scores across CO/UT/ID
2. **Geographic context** - View scores with roads, cities, landmarks for intuition
3. **Multi-scale analysis** - Zoom from state-level to neighborhood-level while maintaining heat map visibility
4. **Interactive analysis** - Adjust parameters, filter by subscore, compare regions without writing code
5. **Accessibility** - Non-technical users should access insights through intuitive GUI
6. **Performance** - API data should be cached to avoid repeated expensive calls; users control refresh

Without a GUI, adoption is limited to data scientists. A beautiful, robust interface democratizes access to AUCS insights.

## What Changes

**Web-Based Visualization Application:**

- Dash + Plotly framework (Python-based, interactive, web-ready)
- H3 hexagon choropleth heat maps (total AUCS + all 7 subscores)
- Multi-layer base maps (streets, cities, landmarks via Mapbox or OpenStreetMap)
- Smooth zoom with heat map persistence (H3 hexes at all zoom levels)
- Color scales with legends (0-100 score range, diverging/sequential palettes)

**Interactive Controls:**

- Subscore selector (EA, LCA, MUHAA, JEA, MORR, CTE, SOU, or Total AUCS)
- Region filter (state, metro area, county, custom bounding box)
- Parameter adjustment (expose key params from CLI: weights, decay, VOT)
- Date/time period selector (if comparing runs)
- Hex detail on hover/click (show score breakdown, top contributors, coordinates)

**CLI Integration:**

- All CLI commands accessible via UI forms (data refresh, recompute scores, export)
- Job submission with progress tracking (long-running operations in background)
- Results auto-update in visualization when jobs complete
- Command history and logs viewable in UI

**Intelligent Caching:**

- Cache all external API responses (Wikipedia, Wikidata, NOAA, FAA, etc.)
- Cache OSRM/OTP2 routing results (travel time matrices)
- Display cache status (last updated, staleness indicators)
- Manual refresh button per data source (user-triggered updates)
- Automatic cache invalidation on data schema changes
- Cache statistics dashboard (hit rate, storage size, oldest entry)

**Advanced Features:**

- Side-by-side comparison mode (compare two runs, regions, or parameter sets)
- Time series visualization (if multiple runs exist)
- Export to PNG, PDF, GeoJSON, or interactive HTML
- Shareable URLs (encode filters/settings in URL for collaboration)
- Responsive design (desktop, tablet, mobile)

**Performance Optimizations:**

- Server-side hex aggregation (don't send 1M hexes to browser)
- Dynamic level-of-detail (show fewer hexes at state zoom, more at neighborhood zoom)
- WebGL rendering for smooth pan/zoom (via Plotly/Pydeck)
- Lazy loading (load visible viewport first, fetch on pan)
- Pre-computed zoom-level aggregations (H3 resolution 6/7/8/9)

## Impact

- Affected specs: `visualization` (new), `caching` (new), `ui-framework` (new)
- Affected code:
  - New: `src/Urban_Amenities2/ui/` (Dash app, layouts, callbacks)
  - New: `src/Urban_Amenities2/cache/` (cache manager, invalidation, stats)
  - New: `src/Urban_Amenities2/viz/` (choropleth, maps, color scales)
  - Modified: `cli/main.py` (add `aucs ui` command to launch server)
  - Modified: All data ingestion modules (integrate cache layer)
- External dependencies:
  - Dash (web framework)
  - Plotly (interactive charts and maps)
  - Dash-Leaflet or Pydeck (map layers)
  - Redis or DiskCache (cache backend)
  - Gunicorn or Uvicorn (production web server)
- **Breaking**: None (UI is additive, does not change existing CLI/outputs)
- Timeline: 4-6 weeks for full-featured UI with caching
- User Experience: Transforms AUCS from "data product" to "decision support tool"
