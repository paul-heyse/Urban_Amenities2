"""Sidebar navigation for the UI."""

from __future__ import annotations

from dash import dcc, html

PAGES = [
    {"path": "/", "label": "Overview", "icon": "fa fa-chart-line"},
    {"path": "/map", "label": "Map Explorer", "icon": "fa fa-map"},
    {"path": "/data", "label": "Data", "icon": "fa fa-database"},
    {"path": "/settings", "label": "Settings", "icon": "fa fa-sliders-h"},
]


def build_sidebar() -> html.Aside:
    links = []
    for page in PAGES:
        links.append(
            dcc.Link(
                className="nav-link",
                href=page["path"],
                children=[html.I(className=page["icon"]), html.Span(page["label"])],
            )
        )
    return html.Aside(className="app-sidebar", children=links)


__all__ = ["build_sidebar"]
