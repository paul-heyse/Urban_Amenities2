"""Validate Dash layout factories use provided contexts."""

from __future__ import annotations

from importlib import import_module, reload

import pytest
from dash import Dash, dcc, html


@pytest.fixture
def layouts_module():
    module = import_module("Urban_Amenities2.ui.layouts")
    return module


@pytest.fixture
def dash_app(ui_settings, layouts_module):
    # Ensure Dash is initialised before pages register themselves
    app = Dash(__name__, use_pages=True, pages_folder="")
    reload(layouts_module)
    app.title = ui_settings.title
    layouts_module.register_layouts(app, ui_settings)
    return app, layouts_module


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
