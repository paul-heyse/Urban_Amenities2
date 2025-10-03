# AUCS 2.0 Interactive UI User Guide

## Overview

The AUCS (Aker Urban Convenience Score) Interactive UI provides a comprehensive web-based interface for exploring urban accessibility scores across Colorado, Utah, and Idaho.

## Getting Started

### Accessing the Application

Navigate to the application URL in your web browser:

- **Development**: `http://localhost:8050`
- **Production**: `<https://aucs.yourdom>

.com`

### System Requirements

- **Desktop**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Tablet**: iPad iOS 14+, Android tablets 10+
- **Mobile**: iPhone iOS 14+, Android 10+
- **Internet**: Minimum 5 Mbps connection recommended

## Main Interface

### Navigation

The application consists of four main sections accessible from the sidebar:

1. **Home**: Overview and quick stats
2. **Map View**: Interactive heat map visualization
3. **Data Management**: Cache and data refresh controls
4. **Settings**: Parameter adjustments and preferences

### Heat Map View

#### Map Controls

- **Zoom**: Use scroll wheel, + / - buttons, or pinch gesture (mobile)
- **Pan**: Click and drag, or swipe (mobile)
- **Fullscreen**: Click fullscreen button in top-right corner
- **Map Style**: Toggle between street, satellite, and dark modes

#### Subscore Selection

Use the dropdown to view different accessibility dimensions:

- **Total AUCS**: Overall urban convenience score (0-100)
- **EA**: Essentials Access (grocery, pharmacy, healthcare, schools)
- **LCA**: Leisure & Culture Access (restaurants, entertainment, parks)
- **MUHAA**: Major Urban Hub & Airport Access
- **JEA**: Jobs & Education Access
- **MORR**: Mobility Options, Reliability & Resilience
- **CTE**: Corridor Trip-Chaining Enrichment
- **SOU**: Seasonal Outdoors Usability

#### Color Scale

- **Green**: High accessibility (80-100)
- **Yellow-Green**: Good accessibility (60-80)
- **Yellow**: Moderate accessibility (40-60)
- **Orange**: Low accessibility (20-40)
- **Red**: Very low accessibility (0-20)

### Filtering Data

#### Geographic Filters

- **State**: Filter by Colorado, Utah, or Idaho
- **Metro Area**: Filter by specific metropolitan areas (Denver, Salt Lake City, Boise, etc.)
- **County**: Filter by county

#### Score Filters

- **Score Range**: Adjust minimum and maximum score thresholds
- **Population Density**: Filter by urban, suburban, or rural areas
- **Land Use**: Filter by land use categories

### Hex Selection

#### Selecting a Hex

1. **Click** on any hex on the map to select it
2. The hex will be highlighted with a bold outline
3. A detail panel will appear showing:
   - Hex ID and location (lat/lon)
   - Total AUCS and all 7 subscores
   - Top 5 contributing amenities
   - Best transportation modes
   - Metro area and county

#### Comparing Hexes

1. Select multiple hexes (up to 5) by clicking them
2. Click "Compare Hexes" button
3. View side-by-side comparison of all selected hexes
4. Export comparison data as CSV or JSON

#### Viewing Nearby Hexes

1. Select a hex
2. Click "Show Neighbors" button
3. See scores for surrounding hexes (1-ring = 6 neighbors)

### Parameter Adjustments

Navigate to **Settings** to adjust model parameters:

#### Subscore Weights

Adjust the relative importance of each subscore (must sum to 100):

- Essentials Access (default: 30%)
- Leisure & Culture Access (default: 18%)
- Major Hubs & Airports (default: 16%)
- Jobs & Education (default: 14%)
- Mobility & Reliability (default: 12%)
- Corridor Enrichment (default: 5%)
- Seasonal Outdoors (default: 5%)

#### Decay Parameters

Adjust travel time decay (alpha) for each mode:

- **Walk**: Default α = 0.15 (rapid decay)
- **Bike**: Default α = 0.10
- **Transit**: Default α = 0.08
- **Car**: Default α = 0.05 (slow decay)

Higher alpha = faster decay = more local-focused scoring

#### Value of Time

Adjust how fares are converted to time equivalents:

- **Weekday**: Default $18/hour
- **Weekend**: Default $15/hour

#### Applying Changes

1. Adjust parameters as desired
2. Click "Recalculate Scores" button
3. Wait for processing (may take 30-60 seconds for large regions)
4. Updated scores will appear on the map

**Note**: Parameter adjustments are temporary and do not persist after page refresh.

### Exporting Data

#### Export Selected Hex

1. Select one or more hexes
2. Click "Export Hex Data" button
3. Choose format:
   - **JSON**: Machine-readable, includes all metadata
   - **CSV**: Spreadsheet-compatible, includes scores and location

#### Export Filtered Region

1. Apply desired filters (state, metro, score range)
2. Click "Export Filtered Data" button in Data Management
3. Choose format:
   - **GeoJSON**: For GIS applications (QGIS, ArcGIS)
   - **CSV**: For Excel or spreadsheet analysis
   - **Shapefile**: For traditional GIS workflows
   - **Parquet**: For Python/R analysis (most efficient)

#### Export Maps

1. Navigate to desired map view
2. Click camera icon (top-right)
3. Choose format:
   - **PNG**: Raster image (good for presentations)
   - **PDF**: Vector format (good for printing)

### Data Management

#### Viewing Cache Status

Navigate to **Data Management** to see:

- Total cache size (current / maximum)
- Cache hit rate (higher is better, target >80%)
- Oldest and newest cached entries
- Per-source cache statistics

#### Refreshing Cached Data

Click "Refresh Cache" button to manually update:

- **Wikipedia**: Venue popularity data
- **Wikidata**: Venue enrichment
- **NOAA**: Climate normals
- **Transitland**: GTFS feed registry
- **Routing**: OSRM/OTP2 travel times

**Note**: Full refresh can take 10-30 minutes depending on data source.

#### Invalidating Cache

If data appears stale or incorrect:

1. Click "Invalidate Cache" button
2. Select data sources to invalidate
3. Click "Confirm"
4. Fresh data will be fetched on next use

## Keyboard Shortcuts

- **`Ctrl + F`**: Focus on filter search box
- **`Ctrl + Z`**: Zoom in
- **`Ctrl + X`**: Zoom out
- **`Ctrl + R`**: Reset map view
- **`Ctrl + E`**: Export current view
- **`Esc`**: Close detail panel or dialog

## Accessibility Features

### Screen Reader Support

- All interactive elements have ARIA labels
- Keyboard navigation fully supported
- Alternative text for all images and icons

### Keyboard Navigation

- **Tab**: Navigate between interactive elements
- **Enter/Space**: Activate buttons and links
- **Arrow keys**: Pan map (when map is focused)

### High Contrast Mode

Enable in Settings → Accessibility → High Contrast Mode

## Troubleshooting

### Map Not Loading

1. Check internet connection
2. Refresh the page (`F5`)
3. Clear browser cache
4. Try different browser

### Slow Performance

1. Reduce zoom level (view fewer hexes)
2. Apply geographic filters to reduce dataset
3. Close other browser tabs
4. Check system resources (CPU, memory)

### Data Appears Incorrect

1. Check data version in Data Management
2. Click "Refresh Cache" to update
3. Verify filters are not excluding expected data
4. Report issue via feedback form

### Export Fails

1. Check that hexes are selected
2. Verify sufficient disk space
3. Try smaller region or fewer hexes
4. Contact support if issue persists

## Developer Notes

- Shared UI data shapes now live in `Urban_Amenities2.ui.types`. TypedDicts cover score rows, geometry cache records, and GeoJSON overlays so mypy can validate inter-module usage.
- `HexGeometryCache` stores `GeometryCacheEntry` dataclasses and always returns DataFrames with `geometry`, `geometry_wkt`, centroid, and resolution columns. Call `ensure_geometries()` before relying on viewport math.
- `DataContext` enforces typed overlays. `get_overlay()` always returns a `FeatureCollection`, and `_load_external_overlays()` drops malformed files instead of propagating raw dictionaries.
- Run `mypy src/Urban_Amenities2/ui --warn-unused-ignores` after modifying UI data loaders to confirm TypedDict updates remain in sync.

## Support

For questions, issues, or feedback:

- **Email**: <support@aucs.example.com>
- **GitHub Issues**: <https://github.com/paulaker/Urban_Amenities2/issues>
- **Documentation**: <https://github.com/paulaker/Urban_Amenities2/docs>

## Version History

- **v0.1.0** (2025-10-02): Initial release with core features
