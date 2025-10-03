"""Map exploration page."""

from __future__ import annotations

from typing import Any, Callable, Sequence, cast

from dash import dcc, html, register_page as _register_page

from ..components.filters import build_filter_panel, build_parameter_panel
from ..components.overlay_controls import build_overlay_panel
from ..config import UISettings
from ..data_loader import DataContext
from ..layers import basemap_options
from ..scores_controls import SUBSCORE_DESCRIPTIONS, SUBSCORE_OPTIONS
from . import DATA_CONTEXT, SETTINGS

register_page = cast(Callable[..., None], _register_page)
register_page(__name__, path="/map", name="Map Explorer")


def _sorted_values(values: Sequence[str]) -> list[str]:
    return sorted({str(value) for value in values})


def _collect_unique(context: DataContext | None, column: str) -> list[str]:
    if context is None or column not in context.scores:
        return []
    values = context.scores[column].dropna().astype(str).tolist()
    return _sorted_values(values)


def layout(**_: object) -> html.Div:
    context = DATA_CONTEXT
    SETTINGS or UISettings.from_environment()
    states = _collect_unique(context, "state")
    metros = _collect_unique(context, "metro")
    counties = _collect_unique(context, "county")
    option_count = len(SUBSCORE_OPTIONS)
    default_weights = {option["value"]: 100 / option_count for option in SUBSCORE_OPTIONS}
    subscore_dropdown_options = [dict(option) for option in SUBSCORE_OPTIONS]
    basemap_dropdown_options = [dict(option) for option in basemap_options()]
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
                        options=cast(Any, subscore_dropdown_options),
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
                        options=cast(Any, basemap_dropdown_options),
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
