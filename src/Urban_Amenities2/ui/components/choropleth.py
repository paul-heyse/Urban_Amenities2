"""Plotly choropleth helpers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
import plotly.graph_objects as go  # type: ignore[import-untyped]
from plotly.basedatatypes import BaseTraceType

from ..contracts import MapboxLayer

COLOR_SCALES: dict[str, str] = {
    "aucs": "Viridis",
    "EA": "YlGn",
    "LCA": "Blues",
    "MUHAA": "OrRd",
    "JEA": "PuRd",
    "MORR": "Plasma",
    "CTE": "Greens",
    "SOU": "Turbo",
}


def create_choropleth(
    *,
    geojson: Mapping[str, object],
    frame: pd.DataFrame,
    score_column: str,
    hover_columns: Iterable[str],
    mapbox_token: str | None,
    center: Mapping[str, float] | None = None,
    zoom: float = 6.0,
    map_style: str = "carto-positron",
    transition_duration: int = 350,
    layers: Sequence[MapboxLayer] | None = None,
    extra_traces: Sequence[BaseTraceType] | None = None,
    attribution: str | None = None,
) -> go.Figure:
    color_scale = COLOR_SCALES.get(score_column, "Viridis")
    hover_columns = list(dict.fromkeys(hover_columns))
    hovertemplate = "<br>".join(
        ["<b>%{customdata[0]}</b>"]
        + [f"{col}: %{{customdata[{i+1}]}}" for i, col in enumerate(hover_columns)]
    )
    figure = go.Figure(
        go.Choroplethmapbox(
            geojson=geojson,
            locations=frame["hex_id"],
            z=frame[score_column],
            colorscale=color_scale,
            marker_opacity=0.85,
            marker_line_width=0,
            customdata=frame[["hex_id", *hover_columns]].to_numpy(),
            hovertemplate=hovertemplate,
            colorbar=dict(title=score_column.upper()),
        )
    )
    mapbox_style = _resolve_style(map_style, mapbox_token)
    default_center: Mapping[str, float] = {"lat": 39.5, "lon": -111.0}
    mapbox_config: dict[str, Any] = {
        "style": mapbox_style,
        "center": dict(center) if center else dict(default_center),
        "zoom": zoom,
    }
    if mapbox_style.startswith("mapbox://") and mapbox_token:
        mapbox_config["accesstoken"] = mapbox_token
    if layers:
        mapbox_config["layers"] = [dict(layer) for layer in layers]
    if extra_traces:
        for trace in extra_traces:
            figure.add_trace(trace)
    figure.update_layout(
        mapbox=mapbox_config,
        margin=dict(l=0, r=0, t=0, b=0),
        transition=dict(duration=transition_duration, easing="cubic-in-out"),
        uirevision="hex-map",
    )
    if attribution:
        annotation: dict[str, Any] = {
            "text": attribution,
            "x": 0,
            "y": 0,
            "xref": "paper",
            "yref": "paper",
            "showarrow": False,
            "xanchor": "left",
            "yanchor": "bottom",
            "font": {"size": 10, "color": "#4b5563"},
            "bgcolor": "rgba(255,255,255,0.65)",
            "borderpad": 4,
        }
        figure.update_layout(annotations=[annotation])
    figure.update_traces(selector={"type": "choroplethmapbox"}, marker={"line": {"width": 0}})
    return figure


def _resolve_style(style: str, token: str | None) -> str:
    if style.startswith("mapbox://") and not token:
        return "open-street-map"
    return style


__all__ = ["create_choropleth"]
