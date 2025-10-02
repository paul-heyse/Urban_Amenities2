# Visualization Specification

## ADDED Requirements

### Requirement: Hex Choropleth Heat Maps

The system SHALL display AUCS scores as interactive hex choropleth heat maps.

#### Scenario: Heat map renders all scores

- **WHEN** user loads map view
- **THEN** hexagons SHALL be colored by AUCS score (0-100)
- **AND** color scale SHALL use sequential or diverging colormap (user-selectable)
- **AND** legend SHALL show score-to-color mapping

#### Scenario: Multi-scale visualization

- **WHEN** user zooms from state to neighborhood level
- **THEN** heat map SHALL remain visible at all zoom levels
- **AND** hex resolution SHALL adjust based on zoom:
  - Zoom 0-5: H3 resolution 6 (large hexes)
  - Zoom 6-8: H3 resolution 7 (medium hexes)
  - Zoom 9-11: H3 resolution 8 (small hexes)
  - Zoom 12+: H3 resolution 9 (finest hexes)
- **AND** transitions SHALL be smooth (fade in/out)

#### Scenario: Subscore selection

- **WHEN** user selects subscore from dropdown (EA, LCA, MUHAA, JEA, MORR, CTE, SOU, or Total AUCS)
- **THEN** heat map SHALL update to show selected subscore
- **AND** legend SHALL update to reflect subscore name
- **AND** color scale SHALL adjust to subscore range

---

### Requirement: Base Map Integration

The system SHALL overlay heat maps on geographic base maps with roads, cities, and landmarks.

#### Scenario: Base map provides context

- **WHEN** viewing heat map
- **THEN** streets and roads SHALL be visible at all zoom levels
- **AND** city labels SHALL appear for major cities (Denver, Salt Lake City, Boise, Colorado Springs, etc.)
- **AND** landmark labels SHALL appear for airports, universities, major parks

#### Scenario: Base map style selection

- **WHEN** user selects base map style
- **THEN** available styles SHALL include: Streets, Outdoors, Satellite, Dark Mode
- **AND** map SHALL update to selected style
- **AND** heat map overlay SHALL remain visible on all styles

#### Scenario: Geographic overlays

- **WHEN** user enables geographic overlays
- **THEN** toggleable layers SHALL include:
  - State boundaries (CO, UT, ID)
  - County boundaries
  - Metro area boundaries
  - Transit lines (from GTFS)
  - Transit stops
  - Protected areas (parks/trails)
- **AND** layer opacity SHALL be adjustable (0-100%)

---

### Requirement: Interactive Map Controls

The system SHALL provide intuitive controls for map navigation and interaction.

#### Scenario: Zoom and pan

- **WHEN** user zooms in/out or pans
- **THEN** map SHALL respond smoothly (<500ms)
- **AND** heat map SHALL update to show hexes in new viewport
- **AND** loading indicator SHALL appear while fetching new hexes

#### Scenario: Hover tooltips

- **WHEN** user hovers over hex
- **THEN** tooltip SHALL display: hex ID, score, metro area, lat/lon
- **AND** tooltip SHALL appear within 200ms
- **AND** tooltip SHALL follow cursor

#### Scenario: Hex selection

- **WHEN** user clicks hex
- **THEN** hex SHALL be highlighted (outline or glow)
- **AND** hex detail modal SHALL open with full score breakdown
- **AND** modal SHALL remain open until user dismisses

---

### Requirement: Performance at Scale

The system SHALL render heat maps efficiently for up to 1 million hexes.

#### Scenario: Fast initial load

- **WHEN** user loads map view
- **THEN** initial render SHALL complete in <2 seconds
- **AND** only hexes in viewport SHALL be sent to browser (5,000-10,000 hexes)
- **AND** loading spinner SHALL appear during data fetch

#### Scenario: Smooth interactions

- **WHEN** user zooms, pans, or filters
- **THEN** UI SHALL respond in <500ms
- **AND** debouncing SHALL prevent excessive re-renders during rapid interactions
- **AND** WebGL rendering SHALL be used for >10,000 hexes

#### Scenario: Viewport-based loading

- **WHEN** user pans to new area
- **THEN** system SHALL fetch hexes for new viewport from backend
- **AND** fetched hexes SHALL be cached in browser (avoid re-fetch on back-pan)
- **AND** fetch SHALL include 0.5× buffer beyond viewport (pre-fetch adjacent areas)

---

### Requirement: Export Capabilities

The system SHALL support exporting maps and data in multiple formats.

#### Scenario: Map image export

- **WHEN** user clicks "Export Map"
- **THEN** export formats SHALL include: PNG, PDF, SVG
- **AND** user SHALL select resolution (72 DPI, 150 DPI, 300 DPI)
- **AND** export SHALL include legend, scale bar, and attribution
- **AND** exported file SHALL be <10MB

#### Scenario: Data export

- **WHEN** user clicks "Export Data"
- **THEN** export formats SHALL include: GeoJSON, CSV, Shapefile, GeoPackage
- **AND** export SHALL apply current filters (only export visible hexes)
- **AND** user SHALL select columns to include
- **AND** coordinate system SHALL be WGS84 (EPSG:4326) or user-selected
- **AND** metadata file SHALL include parameter hash, run date, filters applied

#### Scenario: Large export handling

- **WHEN** exporting >100,000 hexes
- **THEN** progress indicator SHALL show percentage complete
- **AND** export SHALL stream data (not load all in memory)
- **AND** export SHALL complete in <5 minutes for 1M hexes

---

### Requirement: Hex Detail Drill-Down

The system SHALL provide detailed information for individual hexes.

#### Scenario: Hex detail modal

- **WHEN** user clicks hex
- **THEN** modal SHALL display:
  - Total AUCS score (large, prominent)
  - All 7 subscores (bar chart: EA, LCA, MUHAA, JEA, MORR, CTE, SOU)
  - Top 5 accessible amenities (from explainability output)
  - Mode breakdown (walk, bike, transit, car accessibility)
  - Hex metadata (lat/lon, metro area, county)
  - Nearby hexes with scores (table of neighbors)

#### Scenario: Hex comparison

- **WHEN** user selects "Compare Hex" from detail modal
- **THEN** hex SHALL be added to comparison set (max 5 hexes)
- **AND** comparison panel SHALL show side-by-side scores and metadata
- **AND** differences SHALL be highlighted (which hex is better per subscore)

#### Scenario: Hex export

- **WHEN** user clicks "Export Hex Data"
- **THEN** JSON or CSV SHALL be downloaded with hex details
- **AND** file SHALL include all scores, contributors, and metadata

---

### Requirement: Color Scale Configuration

The system SHALL provide intuitive color scales for score visualization.

#### Scenario: Sequential color scale for absolute scores

- **WHEN** viewing total AUCS or subscores
- **THEN** color scale SHALL be sequential (low-to-high: light-to-dark or red-to-green)
- **AND** scale SHALL span full score range (0-100 or actual min-max)
- **AND** user SHALL select from palettes: Viridis, RdYlGn, Blues, Oranges

#### Scenario: Diverging color scale for comparisons

- **WHEN** viewing difference heat map (comparison mode)
- **THEN** color scale SHALL be diverging (negative-to-positive: red-white-blue)
- **AND** midpoint (zero difference) SHALL be neutral color (white or gray)
- **AND** scale SHALL be symmetric around zero

#### Scenario: Custom color scale

- **WHEN** user customizes color scale
- **THEN** user SHALL adjust: min value, max value, number of bins
- **AND** legend SHALL update in real-time
- **AND** custom scale SHALL be savable as preset

---

### Requirement: Responsive Design

The system SHALL function on desktop, tablet, and mobile devices.

#### Scenario: Desktop layout

- **WHEN** viewing on desktop (>1200px width)
- **THEN** layout SHALL show sidebar filters + main map + detail panel
- **AND** all controls SHALL be accessible without scrolling

#### Scenario: Tablet layout

- **WHEN** viewing on tablet (768px-1200px width)
- **THEN** sidebar SHALL collapse to icon menu
- **AND** map SHALL occupy full width
- **AND** detail panel SHALL overlay map when opened

#### Scenario: Mobile layout

- **WHEN** viewing on mobile (<768px width)
- **THEN** filters SHALL be in bottom sheet (swipe up)
- **AND** map SHALL be full-screen
- **AND** hex detail SHALL be full-screen modal
- **AND** all interactions SHALL work with touch gestures

#### Scenario: Touch interactions

- **WHEN** using touch device
- **THEN** pinch-to-zoom SHALL work smoothly
- **AND** tap SHALL select hex (no need for hover)
- **AND** two-finger pan SHALL move map
