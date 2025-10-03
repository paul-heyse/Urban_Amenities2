"""Map exploration page."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, cast

from dash import dcc, html

from ..components.filters import build_filter_panel, build_parameter_panel
from ..components.overlay_controls import build_overlay_panel
from ..config import UISettings
from ..contracts import SubscoreCode
from ..dash_wrappers import register_page
from ..layers import basemap_options
from ..scores_controls import SUBSCORE_DESCRIPTIONS, SUBSCORE_OPTIONS
from . import DATA_CONTEXT, SETTINGS

register_page(__name__, path="/map", name="Map Explorer")


def _as_dropdown_options(options: Sequence[Mapping[str, object]]) -> list[dict[str, str]]:
    payloads: list[dict[str, str]] = []
    for option in options:
        label = option.get("label")
        value = option.get("value")
        if isinstance(label, str) and isinstance(value, str):
            payloads.append({"label": label, "value": value})
    return payloads


def layout(**_: Any) -> html.Div:
    context = DATA_CONTEXT
    settings = SETTINGS or UISettings.from_environment()
    states = (
        sorted(context.scores["state"].dropna().unique())
        if context is not None and "state" in context.scores
        else []
    )
    metros = (
        sorted(context.scores["metro"].dropna().unique())
        if context is not None and "metro" in context.scores
        else []
    )
    counties = (
        sorted(context.scores["county"].dropna().unique())
        if context is not None and "county" in context.scores
        else []
    )
    default_weights: dict[str, float] = {
        str(option["value"]): 100.0 / len(SUBSCORE_OPTIONS) for option in SUBSCORE_OPTIONS
    }
    basemap_choices = basemap_options()
    default_basemap_value = (
        basemap_choices[0]["value"] if basemap_choices else "mapbox://styles/mapbox/streets-v11"
    )
    subscore_default: SubscoreCode = "aucs"
    subscore_dropdown_options = _as_dropdown_options(SUBSCORE_OPTIONS)
    basemap_dropdown_options = _as_dropdown_options(basemap_choices)
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
                        options=cast(Sequence[Any], subscore_dropdown_options),
                        value=subscore_default,
                        id="subscore-select",
                        clearable=False,
                    ),
                    html.Div(
                        SUBSCORE_DESCRIPTIONS[subscore_default],
                        id="subscore-description",
                        className="subscore-description",
                    ),
                    html.Label("Base Map"),
                    dcc.Dropdown(
                        options=cast(Sequence[Any], basemap_dropdown_options),
                        value=default_basemap_value,
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
            html.Small(
                f"Configured title: {settings.title}",
                className="map-settings-hint",
            ),
        ],
    )


__all__ = ["layout"]
