"""Dash callback registrations for the UI."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any, cast

import plotly.graph_objects as go
from dash import Dash, Input, Output, State, callback_context, html, no_update
from dash._no_update import NoUpdate as DashNoUpdate

from .components.choropleth import create_choropleth
from .components.overlay_controls import OVERLAY_OPTIONS
from .config import UISettings
from .contracts import OverlayId, SubscoreCode
from .dash_wrappers import register_callback
from .data_loader import DataContext
from .downloads import send_file
from .export_types import DownloadPayload
from .layers import basemap_attribution, build_overlay_payload, resolve_basemap_style
from .scores_controls import SUBSCORE_DESCRIPTIONS

OVERLAY_IDS: frozenset[OverlayId] = frozenset(option["value"] for option in OVERLAY_OPTIONS)


def _normalise_filters(values: Iterable[str] | str | None) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        return [values]
    return [value for value in values if value]


def _normalise_overlays(values: Iterable[str] | str | None) -> list[OverlayId]:
    candidates = _normalise_filters(values)
    return [cast(OverlayId, value) for value in candidates if value in OVERLAY_IDS]


def _resolution_for_zoom(zoom: float | None) -> int:
    if zoom is None:
        return 8
    if zoom <= 5:
        return 6
    if zoom <= 8:
        return 7
    if zoom <= 11:
        return 8
    return 9


def _extract_viewport_bounds(
    relayout_data: Mapping[str, Any] | None,
    fallback: tuple[float, float, float, float] | None,
) -> tuple[float, float, float, float] | None:
    if not isinstance(relayout_data, Mapping):
        return fallback
    derived = relayout_data.get("mapbox._derived")
    if isinstance(derived, Mapping):
        coordinates = derived.get("coordinates")
        if isinstance(coordinates, Sequence):
            points: list[Sequence[float]] = [
                point
                for ring in coordinates
                if isinstance(ring, Sequence)
                for point in ring
                if isinstance(point, Sequence)
            ]
            if points:
                lons = [float(point[0]) for point in points if len(point) >= 2]
                lats = [float(point[1]) for point in points if len(point) >= 2]
                if lons and lats:
                    return min(lons), min(lats), max(lons), max(lats)
    lon = relayout_data.get("mapbox.center.lon")
    lat = relayout_data.get("mapbox.center.lat")
    zoom_value = relayout_data.get("mapbox.zoom")
    if (
        isinstance(lon, (int, float))
        and isinstance(lat, (int, float))
        and isinstance(zoom_value, (int, float))
    ):
        zoom = float(zoom_value)
        span = max(0.1, 360 / (2 ** max(zoom, 0.0)))
        lon_f = float(lon)
        lat_f = float(lat)
        return lon_f - span, lat_f - span, lon_f + span, lat_f + span
    return fallback


def register_callbacks(app: Dash, data_context: DataContext, settings: UISettings) -> None:
    @register_callback(
        app,
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
        subscore: SubscoreCode,
        basemap: str,
        overlay_values: Iterable[str] | str | None,
        overlay_opacity: float | None,
        *_events: object,
        relayout_data: Mapping[str, Any] | None,
        state_values: Iterable[str] | str | None,
        metro_values: Iterable[str] | str | None,
        county_values: Iterable[str] | str | None,
        score_range: Sequence[float] | None,
    ) -> tuple[go.Figure, str, str]:
        triggered = cast(str | None, getattr(callback_context, "triggered_id", None))
        if triggered == "clear-filters":
            state_values = metro_values = county_values = []
            score_range = (0.0, 100.0)
        score_bounds: tuple[float, float] | None
        if score_range is None or len(score_range) < 2:
            score_bounds = None
        else:
            score_bounds = (float(score_range[0]), float(score_range[1]))
        filtered = data_context.filter_scores(
            state=_normalise_filters(state_values),
            metro=_normalise_filters(metro_values),
            county=_normalise_filters(county_values),
            score_range=score_bounds,
        )
        zoom_value: float | None = None
        if isinstance(relayout_data, Mapping):
            candidate = relayout_data.get("mapbox.zoom")
            if isinstance(candidate, (int, float)):
                zoom_value = float(candidate)
        resolution = _resolution_for_zoom(zoom_value)
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
            _normalise_overlays(overlay_values),
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

    @register_callback(
        app,
        Output("refresh-status", "children"),
        Input("refresh-data", "n_clicks"),
        prevent_initial_call=True,
    )
    def _refresh_data(_n_clicks: int | None) -> html.Span:
        data_context.refresh()
        message = (
            f"Reloaded dataset {data_context.version.identifier}"
            if data_context.version
            else "No dataset found"
        )
        return html.Span(message)

    @register_callback(
        app,
        Output("download-data", "data"),
        Input("export-csv", "n_clicks"),
        Input("export-geojson", "n_clicks"),
        prevent_initial_call=True,
    )
    def _export_data(
        csv_clicks: int | None,
        geojson_clicks: int | None,
    ) -> DownloadPayload | DashNoUpdate:
        triggered = cast(str | None, getattr(callback_context, "triggered_id", None))
        if triggered == "export-csv":
            temp = Path("/tmp/ui-export.csv")
            data_context.export_csv(temp)
            return send_file(temp)
        if triggered == "export-geojson":
            temp = Path("/tmp/ui-export.geojson")
            data_context.export_geojson(temp)
            return send_file(temp)
        return no_update


__all__ = ["register_callbacks"]
