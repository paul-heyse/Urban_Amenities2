"""Unit tests covering lightweight UI component factories."""

from __future__ import annotations

import base64
from pathlib import Path

import pytest
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
from Urban_Amenities2.ui.downloads import build_file_download, send_file
from Urban_Amenities2.ui.performance import PerformanceMonitor, profile_function, timer


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
                tooltip = slider.tooltip
                assert isinstance(tooltip, dict)
                assert tooltip.get("placement") == "bottom"
                assert tooltip.get("always_visible") is False
                slider_components.append(slider)
    assert slider_components


def test_performance_timer_logs(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[tuple[str, dict[str, object]]] = []

    class _Recorder:
        def info(self, event: str, **kwargs: object) -> None:
            events.append((event, kwargs))

    monkeypatch.setattr("Urban_Amenities2.ui.performance.logger", _Recorder())
    with timer("load-data"):
        pass

    assert events and events[0][0] == "operation_timed"
    payload = events[0][1]
    assert payload["operation"] == "load-data"
    assert payload["elapsed_ms"] >= 0.0


def test_profile_function_records_execution(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[tuple[str, dict[str, object]]] = []

    class _Recorder:
        def info(self, event: str, **kwargs: object) -> None:
            events.append((event, kwargs))

    monkeypatch.setattr("Urban_Amenities2.ui.performance.logger", _Recorder())

    @profile_function
    def _sample(value: int) -> int:
        return value * 2

    assert _sample(3) == 6
    assert events and events[0][0] == "function_profiled"
    assert events[0][1]["function"] == "_sample"


def test_performance_monitor_stats() -> None:
    monitor = PerformanceMonitor()
    for value in [5.0, 15.0, 25.0]:
        monitor.record("render", value)

    stats = monitor.get_stats("render")
    assert stats is not None
    assert stats["min"] == 5.0
    assert stats["max"] == 25.0
    assert stats["count"] == 3

    aggregate = monitor.get_all_stats()
    assert "render" in aggregate
    assert aggregate["render"]["p50"] >= 5.0


def test_build_file_download_encodes_content(tmp_path: Path) -> None:
    path = tmp_path / "report.txt"
    path.write_text("hello world", encoding="utf-8")

    payload = build_file_download(path, filename="metrics.txt", mimetype="text/plain")
    assert payload["filename"] == "metrics.txt"
    assert payload["type"] == "text/plain"
    decoded = base64.b64decode(payload["content"].encode("ascii"))
    assert decoded == b"hello world"


def test_send_file_delegates_to_dash(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "data.csv"
    path.write_text("value", encoding="utf-8")

    captured: dict[str, object] = {}

    def _fake_send_file(path_str: str, *, filename: str | None, type: str | None) -> dict[str, object]:
        captured["path"] = path_str
        captured["filename"] = filename
        captured["type"] = type
        return {"content": "ok"}

    monkeypatch.setattr("Urban_Amenities2.ui.downloads.dcc.send_file", _fake_send_file)

    payload = send_file(path, filename="data.csv", content_type="text/csv")
    assert payload == {"content": "ok"}
    assert captured == {
        "path": str(path),
        "filename": "data.csv",
        "type": "text/csv",
    }
