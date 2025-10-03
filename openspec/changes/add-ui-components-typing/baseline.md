# UI Components Typing Baseline (2025-10-03)

## mypy failure snapshot

Command: `python -m mypy src/Urban_Amenities2/ui/components src/Urban_Amenities2/ui/layers.py src/Urban_Amenities2/ui/callbacks.py src/Urban_Amenities2/ui/layouts/__init__.py src/Urban_Amenities2/ui/layouts/home.py src/Urban_Amenities2/ui/layouts/map_view.py src/Urban_Amenities2/ui/layouts/settings.py src/Urban_Amenities2/ui/layouts/data_management.py --warn-unused-ignores`

| Module | Errors | Notes |
| --- | --- | --- |
| `ui/components/choropleth.py` | 5 | Untyped Plotly imports, untyped `frame` argument, generic `dict` usage for geojson/layers |
| `ui/components/overlay_controls.py` | 1 | Checklist `options` typed as list of dicts instead of Dash `Options` sequence |
| `ui/layers.py` | 7 | Plotly stubs missing, multiple `dict` literals without type args |
| `ui/callbacks.py` | 14 | Callbacks lack annotations, decorators untyped, Dash send_file unresolved |
| `ui/layouts/*.py` | 15 | `register_page` untyped, factory functions lack annotations, Dropdown options typed as `list[dict]`, DataTable attr missing |

Totals: 42 errors across 8 files (per mypy output).

## Component + callback contract inventory

### `components.filters`
- `build_filter_panel(states, metros, counties)` expects each arg to be a list of `str`; returns `dash.html.Div` embedding Dropdown/RangeSlider controls. Dropdown `options` should be typed sequences of `DropdownOption` (label/value pairs). Range slider outputs pair of floats.
- `build_parameter_panel(default_weights)` consumes mapping of weight key to numeric default (currently `dict[str, float]` but slider expects `float` within 0-100). Returns `html.Div` with slider controls that emit `float` values via Dash callbacks.

### `components.overlay_controls`
- `OVERLAY_OPTIONS` is list of label/value pairs for overlays; should be expressed via `dash.dcc.Checklist` `Options` typing. `DEFAULT_OVERLAYS` is list of overlay identifiers (`Literal` union). `build_overlay_panel()` returns `html.Div` with `dcc.Checklist` (values -> `list[str]`) and slider for opacity (`float`).

### `components.choropleth`
- `create_choropleth` accepts GeoJSON-like mapping with `FeatureCollection`, Pandas `DataFrame` filtered to `hex_id` + score columns, optional Mapbox layers/traces. Returns `plotly.graph_objects.Figure`. Layers should be typed `Sequence[go.Choroplethmapbox | dict[str, Any]]` but currently bare `dict`.

### `ui.layers`
- Builds overlay Plotly layers from `GeoDataFrame`/`DataFrame` inputs. Exposes helpers like `build_state_layer`, `build_transit_layers`, `build_overlay_layers`, each returning `list[dict[str, Any]]` describing Mapbox `layers`. Need typed alias to describe Mapbox layer dict structure (id, source, type, paint/layout).

### `ui.callbacks`
- Contains Dash callback definitions for filters, map updates, data export. Key callback functions: `_update_filters`, `_update_map`, `_refresh_data`, `_export_data`. Each should expose typed parameters (`list[str]`, `float`, `dash.dependencies.Input/State` wrappers) and typed returns (tuples of `ComponentProps`, `dcc.Download`, etc.). Currently missing annotations and rely on untyped decorators.

### `ui.layouts`
- `home.py`, `map_view.py`, `settings.py`, `data_management.py` register Dash pages and construct layout trees. Each expects typed data contexts:
  - `home.build_layout(data_context)` -> `html.Div`; `data_context` should expose `.summary`, `.metadata`.
  - `map_view.build_layout(filter_options, overlay_options, default_layers)` -> typed props for Dropdown/Checklist and outputs `dash.html.Div`.
  - `settings.build_layout(parameter_defaults)` -> expects mapping of weights/thresholds.
  - `data_management.build_layout(export_options)` -> typed mapping for file exports.

These inventories will guide the TypedDict/enum work and callback annotations in later tasks.

## Post-implementation verification

- Command: `python -m mypy src/Urban_Amenities2/ui/components src/Urban_Amenities2/ui/layers.py src/Urban_Amenities2/ui/callbacks.py src/Urban_Amenities2/ui/layouts/__init__.py src/Urban_Amenities2/ui/layouts/home.py src/Urban_Amenities2/ui/layouts/map_view.py src/Urban_Amenities2/ui/layouts/settings.py src/Urban_Amenities2/ui/layouts/data_management.py --warn-unused-ignores`
- Result: ✅ no issues reported after introducing typed contracts, wrappers, and component updates.
