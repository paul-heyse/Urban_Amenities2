# UI Type Safety Baseline (2025-10-04)

## Dynamic constructs (Task 1.1)
- `ui.data_loader.DataContext` mutates cached overlays (`_aggregation_cache`, `overlays`) and materialises shapely geometries via `HexGeometryCache`.
- Dash callbacks in `ui.callbacks` rely on dynamically assembled Plotly figure dictionaries, callback signatures currently untyped.
- UI components (`ui.components.*`, `ui.layers`) build dropdown options, Mapbox layers, and trace dictionaries ad hoc without helper types.
- Hex selection and export helpers (`ui.hex_selection`, `ui.export`) store state as raw dictionaries and lists populated at runtime.

## Known typing gaps (Task 1.2 / 1.4)
- `DataContext` overlay builders accept `dict[str, Any]` payloads; typed aliases required for map layers and overlay metadata.
- `ui.filters.get_filter_options` returns untyped dictionaries (pending refactor to typed `Mapping` and tuples).
- `ui.layers.build_map_layers` returns heterogeneous list mixing Mapbox layers and layout dicts.
- Dash callbacks in `ui.callbacks` currently accept `*args: Any`; need typed signatures for component properties and return values.

## Shared utilities (Task 1.3 / 1.5)
- `ui.logging.get_logger` wraps structlog but returns `FilteringBoundLogger` (typed) while `ui.logging.get_standard_logger` returns stdlib `Logger`.
- `ui.performance` manipulates dictionaries containing `None` for metrics placeholders.

## Test coverage needs (Task 1.6)
- Add factories for typed UI datasets (filters, export payloads) to avoid ad-hoc dicts in tests.
- Expand tests for `ui.filters.get_filter_options` and `ui.export.serialize_feature_collection` to assert typed return structures.

This snapshot should be updated once typed helpers and factories land in the codebase.
