# Baseline Typing Notes

## 1.1 Mypy Snapshot (Before Refactor)

Command: `python -m mypy src/Urban_Amenities2/ui/data_loader.py src/Urban_Amenities2/ui/hexes.py src/Urban_Amenities2/ui/hex_selection.py --warn-unused-ignores`

- 28 errors reported
  - Missing stubs: `pandas`, `shapely`, `h3`
  - Untyped containers: `dict` usage in `HexGeometryCache.store`, overlays, DataContext caches
  - Unsafe assignments: optional shapely imports, default `None` values for list/dict fields in `HexDetails`
  - STRtree attributes flagged because `_tree`/`_geom_map` not declared in dataclass slots

## 1.2 Data Structure Inventory

- **Score rows** (`DataContext.scores`): require TypedDict capturing AUCS + subscores, optional metadata (state/metro/county), lat/lon, and nested amenity/mode payloads.
- **Metadata rows** (`metadata.parquet`): hex-level descriptors (state, metro, county) joined onto scores, should align with `MetadataRecord` TypedDict.
- **Geometry cache entries** (`HexGeometryCache`): hex_id, GeoJSON string, WKT, centroid lat/lon, resolution.
- **Overlay payloads** (`DataContext.overlays`): GeoJSON FeatureCollections with `label` property for administrative boundaries plus external overlays from disk.
- **Aggregation cache keys** (`DataContext._aggregation_cache`): resolution + tuple of selected columns.
