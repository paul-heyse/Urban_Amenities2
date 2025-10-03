"""Validate Dash layout factories use provided contexts."""

from __future__ import annotations

from importlib import import_module, reload
from pathlib import Path
from typing import Callable

import dash
import pandas as pd
import pytest
from dash import Dash, dcc, html

from Urban_Amenities2.ui.config import UISettings
from Urban_Amenities2.ui.data_loader import DataContext, DatasetVersion
from Urban_Amenities2.ui import callbacks as callbacks_module


@pytest.fixture
def layouts_module():
    module = import_module("Urban_Amenities2.ui.layouts")
    return module


@pytest.fixture
def dash_app(ui_settings, layouts_module, data_context, monkeypatch):
    # Ensure Dash is initialised before pages register themselves
    app = Dash(__name__, use_pages=True, pages_folder="")
    reload(layouts_module)
    app.title = ui_settings.title
    monkeypatch.setattr(layouts_module, "DATA_CONTEXT", data_context)
    monkeypatch.setattr(layouts_module, "SETTINGS", ui_settings)
    layouts_module.register_layouts(app, ui_settings)
    return app, layouts_module


@pytest.fixture
def data_context(ui_settings: UISettings, tmp_path: Path) -> DataContext:
    settings = UISettings(
        host=ui_settings.host,
        port=ui_settings.port,
        debug=ui_settings.debug,
        secret_key=ui_settings.secret_key,
        mapbox_token=ui_settings.mapbox_token,
        cors_origins=ui_settings.cors_origins,
        enable_cors=ui_settings.enable_cors,
        data_path=tmp_path,
        log_level=ui_settings.log_level,
        title=ui_settings.title,
        reload_interval_seconds=ui_settings.reload_interval_seconds,
        hex_resolutions=ui_settings.hex_resolutions,
        summary_percentiles=ui_settings.summary_percentiles,
    )
    context = DataContext(settings=settings)
    scores = pd.DataFrame(
        {
            "hex_id": ["hex1", "hex2"],
            "aucs": [75.0, 55.0],
            "EA": [80.0, 60.0],
            "LCA": [70.0, 50.0],
            "MUHAA": [65.0, 45.0],
            "JEA": [85.0, 65.0],
            "MORR": [72.0, 52.0],
            "CTE": [60.0, 40.0],
            "SOU": [68.0, 48.0],
            "state": ["CO", "UT"],
            "metro": ["Denver", "Salt Lake City"],
            "county": ["Denver", "Salt Lake"],
        }
    )
    context.scores = scores
    context.metadata = scores[["hex_id", "state", "metro", "county"]].copy()
    context.geometries = pd.DataFrame(
        {
            "hex_id": ["hex1", "hex2"],
            "geometry": ["{}", "{}"],
            "geometry_wkt": ["POLYGON((0 0,1 0,1 1,0 1,0 0))", "POLYGON((0 0,1 0,1 1,0 1,0 0))"],
            "centroid_lon": [0.0, 1.0],
            "centroid_lat": [0.0, 1.0],
            "resolution": [9, 9],
        }
    )
    context.version = DatasetVersion(identifier="test", created_at=pd.Timestamp(2024, 1, 1).to_pydatetime(), path=Path("."))
    context.base_resolution = 9
    context.bounds = (-105.0, 39.0, -104.0, 40.0)
    context.overlays = {"states": {"type": "FeatureCollection", "features": []}}
    context._overlay_version = "test"
    context._aggregation_version = "test"
    return context


def test_register_layouts_configures_app(dash_app, ui_settings) -> None:
    app, _ = dash_app
    assert isinstance(app.layout, html.Div)
    assert app.title == ui_settings.title


def test_home_layout_uses_context(dash_app, data_context, monkeypatch) -> None:
    _, layouts_module = dash_app
    home = import_module("Urban_Amenities2.ui.layouts.home")
    monkeypatch.setattr(home, "DATA_CONTEXT", data_context)
    layout = home.layout()
    assert isinstance(layout, html.Div)
    scoreboard = layout.children[2]
    assert isinstance(scoreboard, html.Div)
    assert scoreboard.className == "scoreboard"
    summary_table = layout.children[3]
    assert getattr(summary_table, "id", None) == "summary-table"


def test_data_management_layout_shows_version(dash_app, data_context, ui_settings, monkeypatch) -> None:
    data_management = import_module("Urban_Amenities2.ui.layouts.data_management")
    monkeypatch.setattr(data_management, "DATA_CONTEXT", data_context)
    monkeypatch.setattr(data_management, "SETTINGS", ui_settings)
    layout = data_management.layout()
    assert "Data Management" in layout.children[0].children
    assert data_context.version and data_context.version.identifier in layout.children[1].children


def test_map_view_layout_has_controls(dash_app, data_context, ui_settings, monkeypatch) -> None:
    map_view = import_module("Urban_Amenities2.ui.layouts.map_view")
    monkeypatch.setattr(map_view, "DATA_CONTEXT", data_context)
    monkeypatch.setattr(map_view, "SETTINGS", ui_settings)
    layout = map_view.layout()
    assert isinstance(layout, html.Div)
    controls = layout.children[0]
    filter_panel = controls.children[0]
    assert any(isinstance(child, dcc.Dropdown) for child in filter_panel.children[0].children)
    loading_container = layout.children[1]
    assert isinstance(loading_container.children, dcc.Graph)


def test_settings_layout_lists_configuration(dash_app, ui_settings, monkeypatch) -> None:
    settings = import_module("Urban_Amenities2.ui.layouts.settings")
    monkeypatch.setattr(settings, "SETTINGS", ui_settings)
    layout = settings.layout()
    assert "Settings" in layout.children[0].children
    items = layout.children[1].children
    assert any("Hex resolutions" in item.children[0].children for item in items)


def test_register_layouts_initialises_callbacks(monkeypatch, ui_settings) -> None:
    layouts_module = import_module("Urban_Amenities2.ui.layouts")
    reload(layouts_module)
    app = Dash(__name__, use_pages=True, pages_folder="")

    original_registry = dash.page_registry.copy()
    dash.page_registry.clear()

    configure_calls: list[str] = []
    monkeypatch.setattr(
        layouts_module,
        "configure_logging",
        lambda level: configure_calls.append(level),
    )

    captured: dict[str, object] = {}

    def _fake_register_pages() -> None:
        dash.page_registry["Urban_Amenities2.ui.layouts.home"] = {"module": "home"}

    monkeypatch.setattr(layouts_module, "_register_pages", _fake_register_pages)

    class _DummyContext:
        def __init__(self, settings: UISettings) -> None:
            self.settings = settings

        @classmethod
        def from_settings(cls, settings: UISettings) -> "_DummyContext":
            instance = cls(settings)
            captured["context"] = instance
            captured["settings"] = settings
            return instance

    monkeypatch.setattr(layouts_module, "DataContext", _DummyContext)

    callback_args: dict[str, object] = {}

    def _fake_register_callbacks(app_obj: Dash, context: object, settings: UISettings) -> None:
        callback_args["values"] = (app_obj, context, settings)

    monkeypatch.setattr(
        "Urban_Amenities2.ui.callbacks.register_callbacks",
        _fake_register_callbacks,
    )

    try:
        layouts_module.register_layouts(app, ui_settings)

        assert layouts_module.DATA_CONTEXT is captured["context"]
        assert layouts_module.SETTINGS is ui_settings
        assert configure_calls == [ui_settings.log_level]
        assert callback_args["values"] == (app, captured["context"], ui_settings)
        assert "Urban_Amenities2.ui.layouts.home" in dash.page_registry
        assert isinstance(app.layout, html.Div)
    finally:
        dash.page_registry.clear()
        dash.page_registry.update(original_registry)


def test_update_map_callback_builds_overlay_payload(monkeypatch, ui_settings) -> None:
    captured_callbacks: list[tuple[tuple[object, ...], dict[str, object], Callable[..., object]]] = []

    def _capture_callback(app: Dash, *args: object, **kwargs: object):
        def decorator(func: callable) -> callable:
            captured_callbacks.append((args, kwargs, func))
            return func

        return decorator

    monkeypatch.setattr(
        callbacks_module,
        "register_callback",
        _capture_callback,
    )

    overlay_calls: dict[str, object] = {}

    class _DummyPayload:
        def __init__(self) -> None:
            self.layers = ["layer"]
            self.traces = ["trace"]

    def _fake_overlay(selected, context, *, opacity: float) -> _DummyPayload:
        overlay_calls["selected"] = list(selected)
        overlay_calls["opacity"] = opacity
        overlay_calls["context"] = context
        return _DummyPayload()

    monkeypatch.setattr(callbacks_module, "build_overlay_payload", _fake_overlay)

    choropleth_calls: dict[str, object] = {}

    def _fake_choropleth(**kwargs: object) -> str:
        choropleth_calls.update(kwargs)
        return "figure"

    monkeypatch.setattr(callbacks_module, "create_choropleth", _fake_choropleth)
    monkeypatch.setattr(callbacks_module, "resolve_basemap_style", lambda value: value)
    monkeypatch.setattr(callbacks_module, "basemap_attribution", lambda value: f"attr:{value}")

    class _StubCallbackContext:
        triggered_id = "apply-filters"

    monkeypatch.setattr(callbacks_module, "callback_context", _StubCallbackContext())

    class _StubContext:
        def __init__(self) -> None:
            self.base_resolution = 9
            self.bounds = (-105.0, 39.0, -104.0, 40.0)
            self.scores = pd.DataFrame(
                {
                    "hex_id": ["hex1", "hex2"],
                    "aucs": [75.0, 55.0],
                    "EA": [80.0, 60.0],
                    "state": ["CO", "CO"],
                    "metro": ["Denver", "Denver"],
                    "county": ["Denver", "Jefferson"],
                }
            )
            self.filters: list[tuple[object, ...]] = []
            self.viewport: list[tuple[int, tuple[float, float, float, float] | None]] = []

        def filter_scores(
            self,
            *,
            state: list[str],
            metro: list[str],
            county: list[str],
            score_range: tuple[float, float] | None,
        ) -> pd.DataFrame:
            self.filters.append((state, metro, county, score_range))
            return self.scores.iloc[[0]].copy()

        def frame_for_resolution(
            self, resolution: int, columns: list[str]
        ) -> pd.DataFrame:
            frame = self.scores[columns + ["hex_id"]].copy()
            frame["count"] = 1
            return frame

        def apply_viewport(
            self,
            frame: pd.DataFrame,
            resolution: int,
            bounds: tuple[float, float, float, float] | None,
        ) -> pd.DataFrame:
            self.viewport.append((resolution, bounds))
            return frame.iloc[[0]].copy()

        def attach_geometries(self, frame: pd.DataFrame) -> pd.DataFrame:
            frame = frame.copy()
            frame["centroid_lat"] = 39.7392
            frame["centroid_lon"] = -104.9903
            return frame

        def to_geojson(self, frame: pd.DataFrame) -> dict[str, object]:
            return {"type": "FeatureCollection", "features": []}

        def get_overlay(self, _key: str) -> dict[str, object]:
            return {"type": "FeatureCollection", "features": []}

    stub_context = _StubContext()
    callbacks_module.register_callbacks(Dash(__name__), stub_context, ui_settings)
    assert captured_callbacks

    _, _, update_map = captured_callbacks[0]
    figure, count_text, description = update_map(
        "EA",
        "mapbox://styles/mapbox/streets-v11",
        ["states", "city_labels"],
        0.6,
        None,
        None,
        relayout_data={
            "mapbox.zoom": 9,
            "mapbox._derived": {
                "coordinates": [[[-105.0, 39.0], [-104.0, 39.0], [-104.0, 40.0], [-105.0, 40.0]]]
            },
        },
        state_values=["CO"],
        metro_values=["Denver"],
        county_values=["Denver"],
        score_range=[10.0, 90.0],
    )

    assert figure == "figure"
    assert "Showing" in count_text
    assert description == callbacks_module.SUBSCORE_DESCRIPTIONS["EA"]
    assert set(overlay_calls["selected"]) == {"states", "city_labels"}
    assert overlay_calls["opacity"] == 0.6
    assert choropleth_calls["hover_columns"] == ["EA", "aucs", "count", "centroid_lat", "centroid_lon"]
