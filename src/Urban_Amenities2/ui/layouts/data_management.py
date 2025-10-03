"""Data management page."""

from __future__ import annotations

from typing import Callable, cast

from dash import dcc, html, register_page as _register_page

from ..config import UISettings
from . import DATA_CONTEXT, SETTINGS

register_page = cast(Callable[..., None], _register_page)
register_page(__name__, path="/data", name="Data")


def layout(**_: object) -> html.Div:
    context = DATA_CONTEXT
    SETTINGS or UISettings.from_environment()
    version = context.version.identifier if context and context.version else "Unavailable"
    return html.Div(
        className="page data-page",
        children=[
            html.H2("Data Management"),
            html.P(f"Current dataset: {version}"),
            html.Button("Refresh", id="refresh-data", className="btn btn-primary"),
            html.Div(id="refresh-status", className="refresh-status"),
            html.H3("Export"),
            html.Div(
                className="export-buttons",
                children=[
                    html.Button("Download CSV", id="export-csv", className="btn btn-secondary"),
                    html.Button("Download GeoJSON", id="export-geojson", className="btn btn-secondary"),
                ],
            ),
            dcc.Download(id="download-data"),
        ],
    )


__all__ = ["layout"]
