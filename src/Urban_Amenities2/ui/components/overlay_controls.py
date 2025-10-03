"""UI components for managing map overlay layers."""

from __future__ import annotations

from typing import Any, Sequence, cast

from dash import dcc, html

from ..types import ChecklistOption, OverlayToggle


OVERLAY_OPTIONS: list[ChecklistOption] = [
    {"label": "State boundaries", "value": "states"},
    {"label": "County boundaries", "value": "counties"},
    {"label": "Metro areas", "value": "metros"},
    {"label": "Transit lines", "value": "transit_lines"},
    {"label": "Transit stops", "value": "transit_stops"},
    {"label": "Parks & trails", "value": "parks"},
    {"label": "City labels", "value": "city_labels"},
    {"label": "Landmarks", "value": "landmark_labels"},
]


DEFAULT_OVERLAYS: list[OverlayToggle] = [
    "states",
    "city_labels",
    "landmark_labels",
]


def build_overlay_panel(
    *,
    options: Sequence[ChecklistOption] | None = None,
    default: Sequence[OverlayToggle] | None = None,
) -> html.Div:
    """Render the overlay control panel."""

    source_options = list(options) if options is not None else OVERLAY_OPTIONS
    resolved_options = [dict(option) for option in source_options]
    resolved_default = [str(value) for value in (default or DEFAULT_OVERLAYS)]
    return html.Div(
        className="overlay-panel",
        children=[
            html.Details(
                open=True,
                children=[
                    html.Summary("Map layers"),
                    dcc.Checklist(
                        id="overlay-layers",
                        options=cast(Any, resolved_options),
                        value=resolved_default,
                        inputClassName="overlay-input",
                        labelClassName="overlay-label",
                    ),
                    html.Label("Overlay opacity"),
                    dcc.Slider(
                        id="overlay-opacity",
                        min=0.0,
                        max=1.0,
                        step=0.05,
                        value=0.35,
                    ),
                    html.Div(
                        className="overlay-hint",
                        children="Layers render beneath the heat map except for labels and transit stops.",
                    ),
                ],
            ),
            html.Small(
                "Map data © Mapbox, OpenStreetMap contributors, Maxar, and local transit agencies",
                className="map-attribution",
            ),
        ],
    )


__all__ = ["build_overlay_panel", "DEFAULT_OVERLAYS", "OVERLAY_OPTIONS"]
