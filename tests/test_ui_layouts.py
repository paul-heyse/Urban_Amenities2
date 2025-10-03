"""Validate Dash layout factories use provided contexts."""

from __future__ import annotations

from importlib import import_module, reload
from pathlib import Path

import pandas as pd
import pytest
from dash import Dash, dcc, html

from Urban_Amenities2.ui.config import UISettings
from Urban_Amenities2.ui.data_loader import DataContext, DatasetVersion


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
