"""Footer component."""

from __future__ import annotations

from datetime import UTC, datetime

from dash import html


def build_footer() -> html.Footer:
    return html.Footer(
        className="app-footer",
        children=[
            html.Span(f"© {datetime.now(UTC):%Y} Urban Amenities Initiative"),
            html.Span("Build: v1.0"),
        ],
    )


__all__ = ["build_footer"]
