from __future__ import annotations

import logging
import types

from Urban_Amenities2 import ui as ui_module
from Urban_Amenities2.ui import create_app
from Urban_Amenities2.ui import layouts as layouts_module
from Urban_Amenities2.ui.config import UISettings


def test_create_app_configures_dash_server(monkeypatch) -> None:
    settings = UISettings(
        host="example.com",
        port=9999,
        debug=True,
        secret_key="secret",
        enable_cors=True,
        cors_origins=["https://allowed"],
        title="Test UI",
    )

    class DummyServer:
        def __init__(self) -> None:
            self.config: dict[str, object] = {}
            self.logger = types.SimpleNamespace(handlers=[], level=None)
            self.routes: dict[str, object] = {}

        def route(self, path: str):
            def _decorator(func):
                self.routes[path] = func
                return func

            return _decorator

        def set_logger_level(self, level: object) -> None:
            self.logger.level = level

    class DummyDash:
        def __init__(self, name: str, *, suppress_callback_exceptions: bool, external_stylesheets, use_pages: bool, **kwargs):
            self.init_args = {
                "name": name,
                "suppress_callback_exceptions": suppress_callback_exceptions,
                "external_stylesheets": external_stylesheets,
                "use_pages": use_pages,
                "kwargs": kwargs,
            }
            self.server = DummyServer()
            self.title = ""
            self.server.logger.setLevel = self.server.set_logger_level

    cors_calls: dict[str, object] = {}

    dash_stub = types.SimpleNamespace(
        Dash=DummyDash,
        dcc=types.SimpleNamespace(),
        html=types.SimpleNamespace(),
        page_container="container",
    )
    bootstrap_stub = types.SimpleNamespace(themes=types.SimpleNamespace(FLATLY="theme"))
    cors_stub = types.SimpleNamespace(
        CORS=lambda server, resources: cors_calls.update(resources=resources)
    )

    def fake_import(name: str):
        if name == "dash":
            return dash_stub
        if name == "dash_bootstrap_components":
            return bootstrap_stub
        if name == "flask_cors":
            return cors_stub
        raise AssertionError(name)

    monkeypatch.setattr(ui_module, "import_module", fake_import)

    gunicorn_logger = logging.getLogger("gunicorn.error")
    handler = logging.StreamHandler()
    gunicorn_logger.addHandler(handler)
    previous_level = gunicorn_logger.level

    captured: dict[str, object] = {}
    monkeypatch.setattr(layouts_module, "register_layouts", lambda app, cfg: captured.setdefault("app", app))

    app: DummyDash | None = None
    try:
        app = create_app(settings)
    finally:
        if handler in gunicorn_logger.handlers:
            gunicorn_logger.removeHandler(handler)
        gunicorn_logger.setLevel(previous_level)

    assert app is not None
    assert isinstance(app, DummyDash)
    assert app.title == "Test UI"
    assert app.init_args["external_stylesheets"] == ["theme"]
    assert app.server.config["SERVER_NAME"] == "example.com:9999"
    assert app.server.config["SECRET_KEY"] == "secret"
    assert "/health" in app.server.routes
    assert cors_calls["resources"] == {r"/*": {"origins": settings.cors_origins}}
    assert app.server.logger.handlers is gunicorn_logger.handlers
    assert app.server.logger.level == gunicorn_logger.level
    assert captured["app"] is app
