"""Register Dash pages and layout fragments."""

from __future__ import annotations

from importlib import import_module
from typing import Optional

from dash import Dash, dcc, html, page_container

from ..config import UISettings
from ..data_loader import DataContext
from ..logging import configure_logging

DATA_CONTEXT: DataContext | None = None
SETTINGS: UISettings | None = None


def register_layouts(app: Dash, settings: UISettings) -> None:
    """Initialise Dash pages and common callbacks."""

    global DATA_CONTEXT, SETTINGS
    configure_logging(settings.log_level)
    data_context = DataContext.from_settings(settings)
    DATA_CONTEXT = data_context
    SETTINGS = settings

    from ..components.footer import build_footer
    from ..components.header import build_header
    from ..components.navigation import build_sidebar

    app.layout = html.Div(
        className="app-shell",
        children=[
            build_header(settings),
            html.Div(
                className="app-body",
                children=[
                    build_sidebar(),
                    html.Main(
                        className="app-content",
                        children=[dcc.Location(id="url"), page_container],
                    ),
                ],
            ),
            build_footer(),
        ],
    )

    _register_pages()

    from ..callbacks import register_callbacks

    register_callbacks(app, data_context, settings)


def _register_pages() -> None:
    """Import page modules so that Dash's page registry is populated."""

    import_module("Urban_Amenities2.ui.layouts.home")
    import_module("Urban_Amenities2.ui.layouts.map_view")
    import_module("Urban_Amenities2.ui.layouts.data_management")
    import_module("Urban_Amenities2.ui.layouts.settings")


__all__ = ["register_layouts"]
