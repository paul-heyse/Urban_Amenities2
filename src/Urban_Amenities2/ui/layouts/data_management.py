"""Data management page."""

from __future__ import annotations

from typing import Any

from dash import dcc, html

from ..config import UISettings
from ..dash_wrappers import register_page
from . import DATA_CONTEXT, SETTINGS

register_page(__name__, path="/data", name="Data")


def layout(**_: Any) -> html.Div:
    context = DATA_CONTEXT
    settings = SETTINGS or UISettings.from_environment()
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
            html.Small(
                f"Automatic refresh every {settings.reload_interval_seconds}s",
                className="refresh-hint",
            ),
        ],
    )


__all__ = ["layout"]
