"""Dash callback registrations."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Optional

import pandas as pd
from dash import Input, Output, State, callback_context, dcc, html, no_update

from .components.choropleth import create_choropleth
from .data_loader import DataContext
from .scores_controls import SUBSCORE_DESCRIPTIONS, SUBSCORE_OPTIONS

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


def register_callbacks(app, data_context: DataContext, settings) -> None:
    @app.callback(
        Output("hex-map", "figure"),
        Output("filter-count", "children"),
        Output("subscore-description", "children"),
        Input("subscore-select", "value"),
        Input("basemap-select", "value"),
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
        source = filtered if not filtered.empty else data_context.scores
        if resolution >= 9:
            base_columns = ["hex_id", "aucs", "state", "metro", "county"]
            if subscore not in base_columns:
                base_columns.append(subscore)
            frame = source[base_columns].copy()
            hover_columns = [subscore, "aucs", "state", "metro", "centroid_lat", "centroid_lon"]
        else:
            frame = data_context.aggregate_by_resolution(resolution, columns=["aucs", subscore])
            hover_columns = [subscore, "aucs", "count", "centroid_lat", "centroid_lon"]
        frame = frame.merge(
            data_context.geometries[["hex_id", "centroid_lat", "centroid_lon"]],
            on="hex_id",
            how="left",
        )
        geojson = data_context.to_geojson(frame)
        figure = create_choropleth(
            geojson=geojson,
            frame=frame.fillna(0.0),
            score_column=subscore,
            hover_columns=hover_columns,
            mapbox_token=settings.mapbox_token,
            map_style=basemap,
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
