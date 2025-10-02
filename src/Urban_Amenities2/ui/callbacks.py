"""Dash callback registrations."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Optional

import pandas as pd
from dash import Input, Output, State, callback_context, dcc, html, no_update

from .components.choropleth import create_choropleth
from .data_loader import DataContext
from .scores_controls import SUBSCORE_DESCRIPTIONS, SUBSCORE_OPTIONS
from .layers import basemap_attribution, build_overlay_payload, resolve_basemap_style

SUBSCORE_VALUES = [option["value"] for option in SUBSCORE_OPTIONS]


def _normalise_filters(values: Iterable[str] | None) -> List[str]:
    if not values:
        return []
    if isinstance(values, str):
        return [values]
    return [value for value in values if value]


def _resolution_for_zoom(zoom: Optional[float]) -> int:
    if zoom is None:
        return 8
    if zoom <= 5:
        return 6
    if zoom <= 8:
        return 7
    if zoom <= 11:
        return 8
    return 9


def _extract_viewport_bounds(relayout_data, fallback: Optional[tuple[float, float, float, float]]):
    if not isinstance(relayout_data, dict):
        return fallback
    derived = relayout_data.get("mapbox._derived") if isinstance(relayout_data, dict) else None
    if isinstance(derived, dict):
        coordinates = derived.get("coordinates")
        if coordinates:
            points = [point for ring in coordinates for point in ring]
            if points:
                lons = [point[0] for point in points]
                lats = [point[1] for point in points]
                return min(lons), min(lats), max(lons), max(lats)
    lon = relayout_data.get("mapbox.center.lon")
    lat = relayout_data.get("mapbox.center.lat")
    if lon is not None and lat is not None and "mapbox.zoom" in relayout_data:
        # Fallback heuristic: approximate span based on zoom level
        zoom = relayout_data.get("mapbox.zoom")
        span = max(0.1, 360 / (2 ** max(zoom, 0)))
        return lon - span, lat - span, lon + span, lat + span
    return fallback


def register_callbacks(app, data_context: DataContext, settings) -> None:
    @app.callback(
        Output("hex-map", "figure"),
        Output("filter-count", "children"),
        Output("subscore-description", "children"),
        Input("subscore-select", "value"),
        Input("basemap-select", "value"),
        Input("overlay-layers", "value"),
        Input("overlay-opacity", "value"),
        Input("apply-filters", "n_clicks"),
        Input("clear-filters", "n_clicks"),
        Input("hex-map", "relayoutData"),
        State("state-filter", "value"),
        State("metro-filter", "value"),
        State("county-filter", "value"),
        State("score-range", "value"),
        prevent_initial_call=False,
    )
    def _update_map(
        subscore: str,
        basemap: str,
        overlay_values,
        overlay_opacity,
        *_events,
        relayout_data,
        state_values,
        metro_values,
        county_values,
        score_range,
    ):
        triggered = callback_context.triggered_id
        if triggered == "clear-filters":
            state_values = metro_values = county_values = []
            score_range = [0, 100]
        filtered = data_context.filter_scores(
            state=_normalise_filters(state_values),
            metro=_normalise_filters(metro_values),
            county=_normalise_filters(county_values),
            score_range=tuple(score_range) if score_range else None,
        )
        zoom = None
        if isinstance(relayout_data, dict):
            zoom = relayout_data.get("mapbox.zoom")
        resolution = _resolution_for_zoom(zoom)
        bounds = _extract_viewport_bounds(relayout_data, data_context.bounds)
        base_resolution = data_context.base_resolution or 9
        source = filtered if not filtered.empty else data_context.scores
        if resolution >= base_resolution:
            base_columns = ["hex_id", "aucs", "state", "metro", "county"]
            if subscore not in base_columns:
                base_columns.append(subscore)
            frame = source[base_columns].copy()
            trimmed = data_context.apply_viewport(frame, base_resolution, bounds)
            if not trimmed.empty:
                frame = trimmed
            hover_candidates = [
                subscore,
                "aucs",
                "state",
                "metro",
                "county",
                "centroid_lat",
                "centroid_lon",
            ]
        else:
            frame = data_context.frame_for_resolution(resolution, columns=["aucs", subscore])
            trimmed = data_context.apply_viewport(frame, resolution, bounds)
            if not trimmed.empty:
                frame = trimmed
            hover_candidates = [subscore, "aucs", "count", "centroid_lat", "centroid_lon"]
        frame = data_context.attach_geometries(frame)
        hover_columns = [column for column in hover_candidates if column in frame.columns]
        geojson = data_context.to_geojson(frame)
        basemap_style = resolve_basemap_style(basemap)
        overlay_payload = build_overlay_payload(
            overlay_values or [],
            data_context,
            opacity=overlay_opacity if overlay_opacity is not None else 0.35,
        )
        figure = create_choropleth(
            geojson=geojson,
            frame=frame.fillna(0.0),
            score_column=subscore,
            hover_columns=hover_columns,
            mapbox_token=settings.mapbox_token,
            map_style=basemap_style,
            layers=overlay_payload.layers,
            extra_traces=overlay_payload.traces,
            attribution=basemap_attribution(basemap_style),
        )
        total = len(data_context.scores)
        filtered_count = len(source)
        description = SUBSCORE_DESCRIPTIONS.get(subscore, "")
        return figure, f"Showing {filtered_count:,} of {total:,} hexes", description

    @app.callback(
        Output("refresh-status", "children"),
        Input("refresh-data", "n_clicks"),
        prevent_initial_call=True,
    )
    def _refresh_data(_n_clicks: int | None):
        data_context.refresh()
        return html.Span(f"Reloaded dataset {data_context.version.identifier}" if data_context.version else "No dataset found")

    @app.callback(
        Output("download-data", "data"),
        Input("export-csv", "n_clicks"),
        Input("export-geojson", "n_clicks"),
        prevent_initial_call=True,
    )
    def _export_data(csv_clicks: int | None, geojson_clicks: int | None):
        triggered = callback_context.triggered_id
        if triggered == "export-csv":
            temp = Path("/tmp/ui-export.csv")
            data_context.export_csv(temp)
            return dcc.send_file(str(temp))
        if triggered == "export-geojson":
            temp = Path("/tmp/ui-export.geojson")
            data_context.export_geojson(temp)
            return dcc.send_file(str(temp))
        return no_update


__all__ = ["register_callbacks"]
