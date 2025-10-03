"""Regression coverage for :mod:`Urban_Amenities2.ui.data_loader`."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable

import pandas as pd
import pytest

from Urban_Amenities2.ui.data_loader import DataContext
from tests.ui_factories import make_ui_settings, write_ui_dataset


@pytest.fixture
def shapely_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provide lightweight stand-ins for optional shapely dependencies."""

    class _DummyShape:
        is_empty = False

        def simplify(self, *_args: object, **_kwargs: object) -> "_DummyShape":
            return self

    class _DummyLoader:
        @staticmethod
        def loads(_wkt: str) -> _DummyShape:
            return _DummyShape()

    def _dummy_mapping(_shape: _DummyShape) -> dict[str, object]:
        return {
            "type": "Polygon",
            "coordinates": [[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]]],
        }

    def _dummy_union(shapes: Iterable[_DummyShape]) -> _DummyShape:
        return next(iter(shapes), _DummyShape())

    def _import_stub() -> tuple[object, object, object]:
        return _DummyLoader, _dummy_mapping, _dummy_union

    monkeypatch.setattr(
        "Urban_Amenities2.ui.data_loader._import_shapely_modules",
        _import_stub,
    )


@pytest.fixture
def loaded_context(
    tmp_path: Path,
    sample_hex_ids: list[str],
    shapely_stub: None,
) -> DataContext:
    data_dir = tmp_path / "ui-data"
    data_dir.mkdir()
    write_ui_dataset(
        data_dir,
        "20240201",
        sample_hex_ids,
        ["WA", "OR", "CA"],
        datetime(2024, 2, 1, 12, 0, 0),
        nested=True,
    )
    settings = make_ui_settings(data_dir)
    context = DataContext.from_settings(settings)
    return context


def test_refresh_prefers_latest_score_dataset(
    tmp_path: Path, sample_hex_ids: list[str], shapely_stub: None
) -> None:
    data_dir = tmp_path / "ui-data"
    data_dir.mkdir()
    write_ui_dataset(
        data_dir,
        "20240101",
        sample_hex_ids,
        ["CO", "NE", "CA"],
        datetime(2024, 1, 1, 12, 0, 0),
    )
    write_ui_dataset(
        data_dir,
        "20240301",
        sample_hex_ids,
        ["NY", "NJ", "PA"],
        datetime(2024, 3, 1, 12, 0, 0),
        nested=True,
    )

    settings = make_ui_settings(data_dir)
    context = DataContext.from_settings(settings)

    assert context.version is not None
    assert context.version.identifier == "20240301"
    assert set(context.scores["state"].unique()) == {"NY", "NJ", "PA"}


def test_refresh_handles_missing_scores(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    data_dir = tmp_path / "ui-empty"
    data_dir.mkdir()

    settings = make_ui_settings(data_dir)
    context = DataContext.from_settings(settings)

    captured = capsys.readouterr()
    assert "ui_scores_missing" in captured.out
    assert context.version is None
    assert context.scores.empty
    assert context.metadata.empty


def test_refresh_falls_back_to_global_metadata(
    tmp_path: Path, sample_hex_ids: list[str], shapely_stub: None
) -> None:
    data_dir = tmp_path / "ui-data"
    data_dir.mkdir()
    write_ui_dataset(
        data_dir,
        "20240101",
        sample_hex_ids,
        ["CO", "NE", "CA"],
        datetime(2024, 1, 1, 12, 0, 0),
        nested=True,
    )
    invalid_metadata = pd.DataFrame({"hex_id": sample_hex_ids})
    invalid_metadata.to_parquet(data_dir / "20240101" / "metadata.parquet")

    fallback = pd.DataFrame(
        {
            "hex_id": sample_hex_ids,
            "state": ["CO", "NE", "CA"],
            "metro": ["Denver", "Lincoln", "Los Angeles"],
            "county": ["Denver", "Lancaster", "Los Angeles"],
        }
    )
    fallback.to_parquet(data_dir / "metadata.parquet")

    settings = make_ui_settings(data_dir)
    context = DataContext.from_settings(settings)

    assert not context.metadata.empty
    assert set(context.metadata.columns) >= {"hex_id", "state", "metro", "county"}
    assert context.metadata["state"].tolist() == ["CO", "NE", "CA"]


def test_build_overlays_with_stubbed_shapely(loaded_context: DataContext) -> None:
    states = loaded_context.get_overlay("states")
    assert states["type"] == "FeatureCollection"
    assert states["features"]
    first = states["features"][0]
    assert first["properties"]["label"] in {"WA", "OR", "CA"}


def test_build_overlays_without_shapely(
    tmp_path: Path, sample_hex_ids: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    data_dir = tmp_path / "ui-data"
    data_dir.mkdir()
    write_ui_dataset(
        data_dir,
        "20240101",
        sample_hex_ids,
        ["CO", "NE", "CA"],
        datetime(2024, 1, 1, 12, 0, 0),
    )

    def _missing_shapely() -> tuple[object, object, object]:
        raise ImportError("shapely not installed")

    monkeypatch.setattr(
        "Urban_Amenities2.ui.data_loader._import_shapely_modules",
        _missing_shapely,
    )

    settings = make_ui_settings(data_dir)
    context = DataContext.from_settings(settings)
    context.rebuild_overlays(force=True)

    assert context.get_overlay("states")["features"] == []
    assert context.get_overlay("parks")["features"] == []


def test_frame_for_resolution_uses_cache(loaded_context: DataContext) -> None:
    loaded_context.base_resolution = 9
    key = (7, ("aucs",))

    _ = loaded_context.frame_for_resolution(7, columns=["aucs"])
    sentinel = pd.DataFrame(
        {
            "hex_id": ["cached"],
            "aucs": [1.23],
            "count": [99],
            "centroid_lat": [0.0],
            "centroid_lon": [0.0],
        }
    )
    loaded_context._aggregation_cache[key] = sentinel

    cached = loaded_context.frame_for_resolution(7, columns=["aucs"])
    pd.testing.assert_frame_equal(cached, sentinel.copy())


def test_apply_viewport_filters_bounds(loaded_context: DataContext) -> None:
    base_resolution = loaded_context.base_resolution or 9
    target = loaded_context.geometries.iloc[0]
    bounds = (
        float(target["centroid_lon"]) - 0.001,
        float(target["centroid_lat"]) - 0.001,
        float(target["centroid_lon"]) + 0.001,
        float(target["centroid_lat"]) + 0.001,
    )
    frame = loaded_context.scores[["hex_id", "aucs"]].copy()
    filtered = loaded_context.apply_viewport(frame, base_resolution, bounds)

    assert not filtered.empty
    assert filtered["hex_id"].nunique() == 1
    assert filtered.iloc[0]["hex_id"] == target["hex_id"]

    ids = loaded_context.ids_in_viewport(bounds, resolution=base_resolution)
    assert ids == [str(target["hex_id"])]


def test_attach_geometries_adds_spatial_columns(loaded_context: DataContext) -> None:
    subset = loaded_context.scores[["hex_id", "aucs"]].head(2)
    attached = loaded_context.attach_geometries(subset)
    assert {"centroid_lat", "centroid_lon"}.issubset(attached.columns)
    assert attached["hex_id"].tolist() == subset["hex_id"].tolist()
