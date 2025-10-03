"""Reusable filter controls."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, cast

from dash import dcc, html

from ..types import SliderTooltip


def build_filter_panel(
    states: Sequence[str], metros: Sequence[str], counties: Sequence[str]
) -> html.Div:
    return html.Div(
        className="filter-panel",
        children=[
            html.Details(
                open=True,
                children=[
                    html.Summary("Filters"),
                    dcc.Dropdown(
                        states, multi=True, id="state-filter", placeholder="Select states"
                    ),
                    dcc.Dropdown(
                        metros, multi=True, id="metro-filter", placeholder="Select metro areas"
                    ),
                    dcc.Dropdown(
                        counties, multi=True, id="county-filter", placeholder="Select counties"
                    ),
                    dcc.RangeSlider(0, 100, step=1, value=[0, 100], id="score-range"),
                    html.Div(
                        className="filter-actions",
                        children=[
                            html.Button(
                                "Apply Filters", id="apply-filters", className="btn btn-primary"
                            ),
                            html.Button("Clear", id="clear-filters", className="btn btn-link"),
                        ],
                    ),
                    html.Div(id="filter-count", className="filter-count"),
                ],
            )
        ],
    )


def build_parameter_panel(default_weights: Mapping[str, float]) -> html.Div:
    sliders = []
    for key, value in default_weights.items():
        tooltip_config: SliderTooltip = {"placement": "bottom", "always_visible": False}
        sliders.append(
            html.Div(
                className="parameter-control",
                children=[
                    html.Label(f"{key} weight"),
                    dcc.Slider(
                        0,
                        100,
                        step=1,
                        value=value,
                        id=f"weight-{key}",
                        tooltip=cast(Any, tooltip_config),
                    ),
                ],
            )
        )
    return html.Div(
        className="parameter-panel",
        children=[
            html.H5("Advanced Settings"),
            html.Details(
                open=False,
                children=[
                    html.Summary("Adjust subscore weights"),
                    html.Div(className="parameter-list", children=sliders),
                    html.Div(
                        className="parameter-actions",
                        children=[
                            html.Button(
                                "Recalculate", id="recalculate", className="btn btn-success"
                            ),
                            html.Button("Reset", id="reset-params", className="btn btn-secondary"),
                        ],
                    ),
                ],
            ),
        ],
    )


__all__ = ["build_filter_panel", "build_parameter_panel"]
