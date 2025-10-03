"""UI components for managing map overlay layers."""

from __future__ import annotations

from dash import dcc, html

OVERLAY_OPTIONS = [
    {"label": "State boundaries", "value": "states"},
    {"label": "County boundaries", "value": "counties"},
    {"label": "Metro areas", "value": "metros"},
    {"label": "Transit lines", "value": "transit_lines"},
    {"label": "Transit stops", "value": "transit_stops"},
    {"label": "Parks & trails", "value": "parks"},
    {"label": "City labels", "value": "city_labels"},
    {"label": "Landmarks", "value": "landmark_labels"},
]


DEFAULT_OVERLAYS = ["states", "city_labels", "landmark_labels"]


def build_overlay_panel() -> html.Div:
    """Render the overlay control panel."""

    return html.Div(
        className="overlay-panel",
        children=[
            html.Details(
                open=True,
                children=[
                    html.Summary("Map layers"),
                    dcc.Checklist(
                        id="overlay-layers",
                        options=OVERLAY_OPTIONS,
                        value=DEFAULT_OVERLAYS,
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
