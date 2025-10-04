from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import pytest
from shapely.geometry import LineString, MultiLineString

from Urban_Amenities2.io.overture import transportation


class StubBigQueryJob:
    def __init__(self, frame: pd.DataFrame) -> None:
        self._frame = frame
        self.requested = False

    def result(self) -> StubBigQueryJob:
        self.requested = True
        return self

    def to_dataframe(self, *, create_bqstorage_client: bool = False) -> pd.DataFrame:
        assert create_bqstorage_client is False
        return self._frame


class RecordingClient:
    def __init__(self, frame: pd.DataFrame) -> None:
        self.frame = frame
        self.last_query: str | None = None

    def query(self, query: str, job_config: Any | None = None) -> StubBigQueryJob:
        self.last_query = query
        return StubBigQueryJob(self.frame)


def test_build_transportation_query_with_custom_classes() -> None:
    config = transportation.TransportationBigQueryConfig(project="proj", dataset="dataset")
    query = transportation.build_transportation_query(config, classes=["road", "cycleway"])
    assert "cycleway" in query
    assert "`proj.dataset.transportation_segments`" in query


def test_filter_transportation_limits_to_allowed_classes() -> None:
    frame = pd.DataFrame({"class": ["road", "rail"], "value": [1, 2]})
    filtered = transportation.filter_transportation(frame, classes=["road"])
    assert list(filtered["class"]) == ["road"]


def test_parse_geometry_converts_wkt() -> None:
    wkt = "LINESTRING (0 0, 1 1)"
    frame = pd.DataFrame({"geometry": [wkt]})
    parsed = transportation.parse_geometry(frame)
    assert isinstance(parsed.loc[0, "geometry"], LineString)


def test_index_segments_invokes_lines_to_hex(monkeypatch: pytest.MonkeyPatch) -> None:
    frame = pd.DataFrame({"geometry": [LineString([(0, 0), (1, 1)])]})
    called: dict[str, Any] = {}

    def _fake_lines_to_hex(data: pd.DataFrame, **kwargs: Any) -> pd.DataFrame:
        called["kwargs"] = kwargs
        return data.assign(hex_id=["hex"])

    monkeypatch.setattr(transportation, "lines_to_hex", _fake_lines_to_hex)
    result = transportation.index_segments(frame, resolution=7)
    assert result.loc[0, "hex_id"] == "hex"
    assert called["kwargs"]["resolution"] == 7


def test_determine_modes_sets_boolean_flags() -> None:
    frame = pd.DataFrame({"class": ["road", "footway", "cycleway"]})
    modes = transportation.determine_modes(frame)
    assert bool(modes.loc[0, "mode_car"])
    assert bool(modes.loc[1, "mode_foot"])
    assert bool(modes.loc[2, "mode_bike"])


def test_export_networks_creates_geojson_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    frame = pd.DataFrame(
        {
            "geometry": [LineString([(0, 0), (1, 1)]), LineString([(0, 0), (1, 0)])],
            "mode_car": [True, False],
            "mode_foot": [True, True],
            "mode_bike": [False, True],
        }
    )
    _ = transportation.gpd.GeoDataFrame(frame, geometry="geometry", crs="EPSG:4326")

    saved: list[Path] = []

    def _capture_to_file(self, path: str, driver: str) -> None:  # type: ignore[override]
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("{}", encoding="utf-8")
        saved.append(target)
        assert driver == "GeoJSON"

    monkeypatch.setattr(transportation.gpd.GeoDataFrame, "to_file", _capture_to_file)
    paths = transportation.export_networks(frame, output_root=tmp_path)
    assert set(paths.keys()) == {"car", "foot", "bike"}
    assert all(path.exists() for path in paths.values())
    assert saved


def test_export_mode_geojson_warns_on_empty(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    frame = pd.DataFrame({"geometry": [LineString([(0, 0), (1, 1)])], "mode": [False]})
    _ = transportation.gpd.GeoDataFrame(frame, geometry="geometry", crs="EPSG:4326")

    def _dummy_to_file(self, path: str, driver: str) -> None:  # type: ignore[override]
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text("{}", encoding="utf-8")

    monkeypatch.setattr(transportation.gpd.GeoDataFrame, "to_file", _dummy_to_file)
    captured: list[dict[str, object]] = []

    def _record_warning(event: str, **kwargs: object) -> None:
        captured.append({"event": event, **kwargs})

    monkeypatch.setattr(transportation.LOGGER, "warning", _record_warning)
    transportation.export_mode_geojson(frame, tmp_path / "network.geojson", "mode")
    assert any(entry.get("event") == "empty_network_export" for entry in captured)


def test_prepare_transportation_filters_and_sets_modes(monkeypatch: pytest.MonkeyPatch) -> None:
    data = pd.DataFrame(
        {
            "class": ["road", "rail"],
            "geometry": [LineString([(0, 0), (1, 1)]), LineString([(0, 0), (1, 1)])],
        }
    )
    monkeypatch.setattr(transportation, "filter_transportation", lambda frame, classes=None: frame[frame["class"] == "road"])
    prepared = transportation.prepare_transportation(data)
    assert set(["mode_car", "mode_foot", "mode_bike"]).issubset(prepared.columns)


def test_read_transportation_from_bigquery_uses_client_query() -> None:
    frame = pd.DataFrame({"id": ["1"], "class": ["road"], "geometry": ["LINESTRING (0 0, 1 1)"]})
    client = RecordingClient(frame)
    config = transportation.TransportationBigQueryConfig(project="proj", dataset="data")
    result = transportation.read_transportation_from_bigquery(config, client=client)  # type: ignore[arg-type]
    assert not result.empty
    assert client.last_query is not None and "transportation_segments" in client.last_query


def test_parse_geometry_rejects_non_linestring() -> None:
    frame = pd.DataFrame({"geometry": [MultiLineString([[(0, 0), (1, 1)], [(1, 1), (2, 2)]])]})
    with pytest.raises(TypeError):
        transportation.parse_geometry(frame)


def test_index_segments_passes_resolution(monkeypatch: pytest.MonkeyPatch) -> None:
    frame = pd.DataFrame({"geometry": [LineString([(0, 0), (1, 1)])]})
    captured: dict[str, Any] = {}

    def _fake_lines_to_hex(data: pd.DataFrame, **kwargs: Any) -> pd.DataFrame:
        captured["kwargs"] = kwargs
        return data.assign(hex_id=["hex"])

    monkeypatch.setattr(transportation, "lines_to_hex", _fake_lines_to_hex)
    transportation.index_segments(frame, resolution=8)
    assert captured["kwargs"]["resolution"] == 8


def test_prepare_transportation_converts_string_geometry() -> None:
    data = pd.DataFrame({"class": ["road"], "geometry": ["LINESTRING (0 0, 1 1)"]})
    prepared = transportation.prepare_transportation(data)
    assert isinstance(prepared.loc[0, "geometry"], LineString)


def test_export_mode_geojson_skips_when_no_mode(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    frame = pd.DataFrame({"geometry": [LineString([(0, 0), (1, 1)])], "mode_car": [False]})
    _ = transportation.gpd.GeoDataFrame(frame, geometry="geometry", crs="EPSG:4326")

    called: dict[str, Any] = {}

    def _capture_warning(event: str, **kwargs: object) -> None:
        called["event"] = event
        called["kwargs"] = kwargs

    def _noop_to_file(self, path: str, driver: str) -> None:  # type: ignore[override]
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text("{}", encoding="utf-8")

    monkeypatch.setattr(transportation.LOGGER, "warning", _capture_warning)
    monkeypatch.setattr(transportation.gpd.GeoDataFrame, "to_file", _noop_to_file)
    transportation.export_mode_geojson(frame, tmp_path / "network.geojson", "mode_car")
    assert called.get("event") == "empty_network_export"
