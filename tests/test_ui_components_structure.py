"""Unit tests covering lightweight UI component factories."""

from __future__ import annotations

from dash import dcc, html

from Urban_Amenities2.ui.components.footer import build_footer
from Urban_Amenities2.ui.components.header import build_header
from Urban_Amenities2.ui.components.navigation import PAGES, build_sidebar
from Urban_Amenities2.ui.components.overlay_controls import (
    DEFAULT_OVERLAYS,
    OVERLAY_OPTIONS,
    build_overlay_panel,
)
from Urban_Amenities2.ui.config import UISettings


def test_build_header_uses_settings(ui_settings: UISettings) -> None:
    header = build_header(ui_settings)
    assert isinstance(header, html.Header)
    assert header.className == "app-header"
    logo_container = header.children[0]
    assert isinstance(logo_container, html.Div)
    assert logo_container.children[1].children == ui_settings.title


def test_build_footer_annotations(monkeypatch) -> None:
    footer = build_footer()
    assert isinstance(footer, html.Footer)
    assert "Urban Amenities Initiative" in footer.children[0].children
    assert footer.children[1].children == "Build: v1.0"


def test_build_sidebar_links() -> None:
    sidebar = build_sidebar()
    assert isinstance(sidebar, html.Aside)
    assert len(sidebar.children) == len(PAGES)
    first_link = sidebar.children[0]
    assert isinstance(first_link, dcc.Link)
    assert first_link.children[1].children == PAGES[0]["label"]


def test_build_overlay_panel_defaults() -> None:
    panel = build_overlay_panel()
    assert isinstance(panel, html.Div)
    details = panel.children[0]
    checklist = details.children[1]
    assert isinstance(checklist, dcc.Checklist)
    assert checklist.value == list(DEFAULT_OVERLAYS)
    option_values = {option["value"] for option in OVERLAY_OPTIONS}
    assert option_values >= set(DEFAULT_OVERLAYS)
    assert all(isinstance(option["label"], str) for option in OVERLAY_OPTIONS)


def test_filter_and_parameter_panels() -> None:
    from Urban_Amenities2.ui.components.filters import (
        build_filter_panel,
        build_parameter_panel,
    )

    filter_panel = build_filter_panel(["CO"], ["Denver"], ["Denver County"])
    assert isinstance(filter_panel.children[0], html.Details)
    dropdowns = [child for child in filter_panel.children[0].children if isinstance(child, dcc.Dropdown)]
    assert len(dropdowns) == 3

    weights = {"aucs": 50.0, "ea": 50.0}
    parameter_panel = build_parameter_panel(weights)
    assert any(isinstance(child, html.Details) for child in parameter_panel.children)
    slider_components: list[dcc.Slider] = []
    for section in parameter_panel.children:
        if not isinstance(section, html.Details):
            continue
        parameter_list = next(
            (child for child in section.children if isinstance(child, html.Div) and child.className == "parameter-list"),
            None,
        )
        assert parameter_list is not None
        for block in parameter_list.children:
            if isinstance(block, html.Div) and len(block.children) == 2:
                slider = block.children[1]
                assert isinstance(slider, dcc.Slider)
                slider_components.append(slider)
    assert slider_components
