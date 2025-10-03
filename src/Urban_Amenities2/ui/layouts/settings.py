"""Settings page for environment configuration."""

from __future__ import annotations

from typing import Any

from dash import html

from ..config import UISettings
from ..dash_wrappers import register_page
from . import SETTINGS

register_page(__name__, path="/settings", name="Settings")


def layout(**_: Any) -> html.Div:
    settings = SETTINGS or UISettings.from_environment()
    items = [
        ("Host", settings.host),
        ("Port", str(settings.port)),
        ("Debug", "yes" if settings.debug else "no"),
        ("Data path", str(settings.data_path)),
        ("CORS origins", ", ".join(settings.cors_origins)),
        ("Reload interval", f"{settings.reload_interval_seconds}s"),
        ("Hex resolutions", ", ".join(str(r) for r in settings.hex_resolutions)),
    ]
    return html.Div(
        className="page settings-page",
        children=[
            html.H2("Settings"),
            html.Ul([html.Li([html.Strong(label), f": {value}"]) for label, value in items]),
        ],
    )


__all__ = ["layout"]
