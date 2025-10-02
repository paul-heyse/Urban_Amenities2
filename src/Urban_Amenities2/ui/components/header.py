"""Header component for the Dash UI."""

from __future__ import annotations

from dash import html

from ..config import UISettings


def build_header(settings: UISettings) -> html.Header:
    return html.Header(
        className="app-header",
        children=[
            html.Div(className="brand", children=[html.Img(src="/assets/logo.svg", className="logo"), html.H1(settings.title)]),
            html.Div(
                className="user-info",
                children=[
                    html.Span("Signed in as data analyst", className="user-name"),
                    html.Button("Feedback", className="btn btn-outline-light", id="feedback-button"),
                ],
            ),
        ],
    )


__all__ = ["build_header"]
