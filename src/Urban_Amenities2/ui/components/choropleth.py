"""Plotly choropleth helpers."""

from __future__ import annotations

from typing import Iterable, Sequence

import plotly.graph_objects as go

COLOR_SCALES = {
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
    geojson: dict,
    frame,
    score_column: str,
    hover_columns: Iterable[str],
    mapbox_token: str | None,
    center: dict[str, float] | None = None,
    zoom: float = 6.0,
    map_style: str = "carto-positron",
    transition_duration: int = 350,
    layers: Sequence[dict] | None = None,
    extra_traces: Sequence[go.BaseTraceType] | None = None,
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
    mapbox_config: dict = {
        "style": mapbox_style,
        "center": center or {"lat": 39.5, "lon": -111.0},
        "zoom": zoom,
    }
    if mapbox_style.startswith("mapbox://") and mapbox_token:
        mapbox_config["accesstoken"] = mapbox_token
    if layers:
        mapbox_config["layers"] = list(layers)
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
        figure.update_layout(
            annotations=[
                dict(
                    text=attribution,
                    x=0,
                    y=0,
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                    xanchor="left",
                    yanchor="bottom",
                    font=dict(size=10, color="#4b5563"),
                    bgcolor="rgba(255,255,255,0.65)",
                    borderpad=4,
                )
            ]
        )
    figure.update_traces(selector=dict(type="choroplethmapbox"), marker=dict(line=dict(width=0)))
    return figure


def _resolve_style(style: str, token: str | None) -> str:
    if style.startswith("mapbox://") and not token:
        return "open-street-map"
    return style


__all__ = ["create_choropleth"]
