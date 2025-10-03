from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pandas as pd
import pytest

from Urban_Amenities2.ui import data_loader
from Urban_Amenities2.ui.config import UISettings
from Urban_Amenities2.ui.data_loader import DataContext


def _settings(data_path: Path) -> UISettings:
    return UISettings(
        host="127.0.0.1",
        port=8050,
        debug=False,
        secret_key="test",
        mapbox_token=None,
        cors_origins=[],
        enable_cors=False,
        data_path=data_path,
        log_level="INFO",
        title="UI Test",
        reload_interval_seconds=30,
        hex_resolutions=[7, 8, 9],
        summary_percentiles=[5, 50, 95],
    )


def _build_scores(hex_ids: list[str], aucs: list[float]) -> pd.DataFrame:
    states = ["CO" if idx % 2 == 0 else "UT" for idx in range(len(hex_ids))]
    frame = pd.DataFrame(
        {
            "hex_id": hex_ids,
            "aucs": aucs,
            "EA": [value - 1 for value in aucs],
            "LCA": [value - 2 for value in aucs],
            "MUHAA": [value - 3 for value in aucs],
            "JEA": [value - 4 for value in aucs],
            "MORR": [value - 5 for value in aucs],
            "CTE": [value - 6 for value in aucs],
            "SOU": [value - 7 for value in aucs],
        }
    )
    return frame


def _parquet_frames(data_dir: Path) -> dict[str, pd.DataFrame]:
    older_scores = data_dir / "20240101_scores.parquet"
    newer_scores = data_dir / "20240201_scores.parquet"
    older_scores.touch()
    newer_scores.touch()
    now = time.time()
    os.utime(older_scores, (now - 60, now - 60))
    os.utime(newer_scores, (now, now))
    older_meta = data_dir / "20240101_metadata.parquet"
    older_meta.touch()
    fallback_meta = data_dir / "metadata.parquet"
    fallback_meta.touch()

    frames: dict[str, pd.DataFrame] = {
        str(older_scores): _build_scores(["abc123", "def456"], [70.0, 60.0]),
        str(newer_scores): _build_scores(["abc123", "ghi789"], [75.0, 65.0]),
        str(older_meta): pd.DataFrame(
            {
                "hex_id": ["abc123", "def456"],
                "state": ["CO", "UT"],
                "metro": ["Denver", "Salt Lake"],
                "county": ["Denver", "Salt Lake"],
            }
        ),
        str(fallback_meta): pd.DataFrame(
            {
                "hex_id": ["abc123", "ghi789"],
                "state": ["CO", "UT"],
                "metro": ["Denver", "Salt Lake"],
                "county": ["Denver", "Salt Lake"],
            }
        ),
    }
    return frames


@pytest.fixture
def ui_dataset(tmp_path: Path) -> tuple[Path, dict[str, pd.DataFrame]]:
    data_dir = tmp_path / "ui"
    data_dir.mkdir()
    overlays = data_dir / "overlays"
    overlays.mkdir()
    (overlays / "transit_lines.geojson").write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [[-105.0, 39.7], [-104.9, 39.8]],
                        },
                        "properties": {"label": "Line"},
                    }
                ],
            }
        )
    )
    frames = _parquet_frames(data_dir)
    return data_dir, frames


def test_data_context_version_switching(
    ui_dataset: tuple[Path, dict[str, pd.DataFrame]],
    monkeypatch: pytest.MonkeyPatch,
    fake_h3,
    fake_shapely,
) -> None:
    data_dir, frames = ui_dataset

    def fake_parquet_loader(self: DataContext, path: Path, columns=None):
        key = str(path)
        frame = frames[key]
        result = frame.copy()
        if columns:
            cols = [column for column in columns if column in result.columns]
            result = result.loc[:, cols]
        if "hex_id" in result.columns:
            result["hex_id"] = result["hex_id"].astype("category")
        return result

    monkeypatch.setattr(DataContext, "_load_parquet", fake_parquet_loader)

    shapely_wkt, mapping, unary_union = data_loader._import_shapely_modules()
    assert hasattr(shapely_wkt, "loads")
    assert callable(mapping)
    assert callable(unary_union)

    context = DataContext.from_settings(_settings(data_dir))
    assert context.version is not None
    assert context.version.identifier == "20240201"
    available = {version.identifier for version in context.available_versions()}
    assert available == {"20240201", "20240101"}

    # Overlays use patched shapely helpers and external overlay files.
    states = context.get_overlay("states")
    assert states["features"]
    assert {feature["properties"]["label"] for feature in states["features"]} == {"CO", "UT"}

    assert context.load_version("20240101") is True
    assert context.version is not None and context.version.identifier == "20240101"
    assert context.scores["aucs"].tolist() == [70.0, 60.0]

    # Aggregation cache resets when switching versions.
    context.frame_for_resolution(7, columns=["aucs"])
    assert context._aggregation_cache
    context.load_version("20240201")
    assert context._aggregation_cache == {}


def test_data_context_viewport_and_exports(
    ui_dataset: tuple[Path, dict[str, pd.DataFrame]],
    monkeypatch: pytest.MonkeyPatch,
    fake_h3,
    fake_shapely,
    tmp_path: Path,
) -> None:
    data_dir, frames = ui_dataset

    def fake_parquet_loader(self: DataContext, path: Path, columns=None):
        frame = frames[str(path)].copy()
        if columns:
            cols = [column for column in columns if column in frame.columns]
            frame = frame.loc[:, cols]
        if "hex_id" in frame.columns:
            frame["hex_id"] = frame["hex_id"].astype("category")
        return frame

    monkeypatch.setattr(DataContext, "_load_parquet", fake_parquet_loader)
    context = DataContext.from_settings(_settings(data_dir))

    base_resolution = context.base_resolution
    assert base_resolution == 9
    high_res = context.frame_for_resolution(base_resolution, columns=["aucs", "EA"])
    assert set(high_res.columns) >= {"hex_id", "aucs", "EA"}

    coarse = context.frame_for_resolution(7, columns=["aucs"])
    assert {"hex_id", "aucs", "count"}.issubset(coarse.columns)

    repeat = context.frame_for_resolution(7, columns=["aucs"])
    assert repeat.equals(coarse)
    assert repeat is not coarse  # cached copy returned

    first = context.geometries.iloc[0]
    delta = 0.0001
    bounds = (
        float(first["centroid_lon"]) - delta,
        float(first["centroid_lat"]) - delta,
        float(first["centroid_lon"]) + delta,
        float(first["centroid_lat"]) + delta,
    )

    trimmed = context.apply_viewport(high_res, base_resolution, bounds)
    assert len(trimmed) >= 1
    assert set(trimmed["hex_id"]) <= set(high_res["hex_id"])  # filtered subset

    ids = context.ids_in_viewport(bounds, resolution=base_resolution)
    assert ids and all(isinstance(item, str) for item in ids)

    attached = context.attach_geometries(high_res)
    assert {"centroid_lat", "centroid_lon"}.issubset(attached.columns)

    index = context.get_hex_index(7)
    assert index

    subset = context.load_subset(["hex_id", "aucs", "aucs"])
    assert list(subset.columns) == ["hex_id", "aucs"]

    geojson_path = tmp_path / "export.geojson"
    context.export_geojson(geojson_path)
    payload = json.loads(geojson_path.read_text())
    assert payload["features"]

    csv_path = tmp_path / "export.csv"
    context.export_csv(csv_path)
    assert csv_path.exists()


def test_data_context_handles_missing_shapely(
    ui_dataset: tuple[Path, dict[str, pd.DataFrame]],
    monkeypatch: pytest.MonkeyPatch,
    fake_h3,
) -> None:
    data_dir, frames = ui_dataset

    def fake_parquet_loader(self: DataContext, path: Path, columns=None):
        frame = frames[str(path)].copy()
        if columns:
            cols = [column for column in columns if column in frame.columns]
            frame = frame.loc[:, cols]
        if "hex_id" in frame.columns:
            frame["hex_id"] = frame["hex_id"].astype("category")
        return frame

    monkeypatch.setattr(DataContext, "_load_parquet", fake_parquet_loader)

    from Urban_Amenities2.ui import data_loader as module

    def raise_modules() -> None:
        raise ImportError("missing shapely")

    monkeypatch.setattr(module, "_import_shapely_modules", raise_modules)

    context = DataContext.from_settings(_settings(data_dir))
    context.rebuild_overlays(force=True)
    assert context.get_overlay("states")["features"] == []
