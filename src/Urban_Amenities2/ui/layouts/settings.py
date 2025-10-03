"""Settings page for environment configuration."""

from __future__ import annotations

from typing import Callable, cast

from dash import html, register_page as _register_page

from ..config import UISettings
from . import SETTINGS

register_page = cast(Callable[..., None], _register_page)
register_page(__name__, path="/settings", name="Settings")


def layout(**_: object) -> html.Div:
    settings = SETTINGS or UISettings.from_environment()
    items = [
        ("Host", settings.host),
        ("Port", settings.port),
        ("Debug", str(settings.debug)),
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
