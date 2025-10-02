"""Map exploration page."""

from __future__ import annotations

from dash import dcc, html, register_page

from ..config import UISettings
from ..scores_controls import SUBSCORE_OPTIONS, SUBSCORE_DESCRIPTIONS
from ..components.filters import build_filter_panel, build_parameter_panel
from ..components.overlay_controls import build_overlay_panel
from ..layers import basemap_options
from . import DATA_CONTEXT, SETTINGS

register_page(__name__, path="/map", name="Map Explorer")


def layout(**_) -> html.Div:
    context = DATA_CONTEXT
    settings = SETTINGS or UISettings.from_environment()
    states = sorted(context.scores["state"].dropna().unique()) if context and "state" in context.scores else []
    metros = sorted(context.scores["metro"].dropna().unique()) if context and "metro" in context.scores else []
    counties = sorted(context.scores["county"].dropna().unique()) if context and "county" in context.scores else []
    default_weights = {option["value"]: 100 / len(SUBSCORE_OPTIONS) for option in SUBSCORE_OPTIONS}
    return html.Div(
        className="page map-page",
        children=[
            html.Div(
                className="map-controls",
                children=[
                    build_filter_panel(states, metros, counties),
                    build_parameter_panel(default_weights),
                    html.Label("Subscore"),
                    dcc.Dropdown(
                        options=SUBSCORE_OPTIONS,
                        value="aucs",
                        id="subscore-select",
                        clearable=False,
                    ),
                    html.Div(
                        SUBSCORE_DESCRIPTIONS["aucs"],
                        id="subscore-description",
                        className="subscore-description",
                    ),
                    html.Label("Base Map"),
                    dcc.Dropdown(
                        options=basemap_options(),
                        value="mapbox://styles/mapbox/streets-v11",
                        id="basemap-select",
                        clearable=False,
                    ),
                    build_overlay_panel(),
                ],
            ),
            dcc.Loading(
                id="map-loading",
                type="circle",
                children=dcc.Graph(id="hex-map", config={"displayModeBar": False}),
            ),
        ],
    )


__all__ = ["layout"]
