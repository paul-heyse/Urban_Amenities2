"""Dash-based interactive user interface for the Urban Amenities model."""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from typing import Any, cast

from .config import UISettings

__all__ = ["UISettings", "create_app"]


def create_app(settings: UISettings | None = None, **overrides: dict[str, Any]) -> Any:
    """Create and configure the Dash application.

    Parameters
    ----------
    settings:
        Optional UI settings. When omitted the configuration is loaded from
        the process environment using :class:`UISettings` defaults.
    **overrides:
        Keyword overrides applied to the Dash initialisation parameters.

    Returns
    -------
    Any
        The initialised Dash application instance. The concrete return type is
        ``dash.Dash`` but Dash is imported lazily so that the backend remains
        optional for non-UI contexts (e.g. batch scoring).
    """

    settings = settings or UISettings.from_environment()
    dash = import_module("dash")
    dash_bootstrap_components = import_module("dash_bootstrap_components")

    external_stylesheets = overrides.pop(
        "external_stylesheets",
        [dash_bootstrap_components.themes.FLATLY],
    )

    app = dash.Dash(
        __name__,
        suppress_callback_exceptions=True,
        external_stylesheets=external_stylesheets,
        use_pages=True,
        **overrides,
    )
    app.title = settings.title

    # Configure Flask server behaviour (logging, health check, CORS)
    server = app.server
    _configure_server(server, settings)

    from .layouts import register_layouts

    register_layouts(app, settings)

    return app


def _configure_server(server: Any, settings: UISettings) -> None:
    """Configure Flask server integration for the Dash application."""

    from flask import Response

    server.config.setdefault("SERVER_NAME", f"{settings.host}:{settings.port}")
    server.config.setdefault("SECRET_KEY", settings.secret_key)

    if settings.enable_cors:
        cors_module = import_module("flask_cors")
        cors_module.CORS(server, resources={r"/*": {"origins": settings.cors_origins}})

    route = cast(Callable[[str], Callable[[Callable[..., Response]], Callable[..., Response]]], server.route)

    @route("/health")
    def _healthcheck() -> Response:  # pragma: no cover - simple HTTP response
        return Response("OK", status=200, mimetype="text/plain")

    import logging

    gunicorn_logger = logging.getLogger("gunicorn.error")
    if gunicorn_logger.handlers:
        server.logger.handlers = gunicorn_logger.handlers
        server.logger.setLevel(gunicorn_logger.level)

