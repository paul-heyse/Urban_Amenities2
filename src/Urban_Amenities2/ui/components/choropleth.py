"""Plotly choropleth helpers."""

from __future__ import annotations

from typing import Iterable

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
            marker_opacity=0.8,
            marker_line_width=0,
            customdata=frame[["hex_id", *hover_columns]].to_numpy(),
            hovertemplate=hovertemplate,
            colorbar=dict(title=score_column.upper()),
        )
    )
    figure.update_layout(
        mapbox_style=map_style,
        mapbox_accesstoken=mapbox_token,
        mapbox_center=center or {"lat": 39.5, "lon": -111.0},
        mapbox_zoom=zoom,
        margin=dict(l=0, r=0, t=0, b=0),
    )
    return figure


__all__ = ["create_choropleth"]
