from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from Urban_Amenities2.ui.config import UISettings
from Urban_Amenities2.ui.data_loader import DataContext
from Urban_Amenities2.ui.hexes import HexGeometryCache


def test_hex_geometry_cache_caches_entries() -> None:
    cache = HexGeometryCache()
    hex_ids = ["8928308280fffff", "8928308280fffff"]
    frame = cache.ensure_geometries(hex_ids)
    assert set(frame.columns) >= {
        "hex_id",
        "geometry",
        "geometry_wkt",
        "centroid_lon",
        "centroid_lat",
        "resolution",
    }
    cached_frame = cache.ensure_geometries(hex_ids)
    assert len(cached_frame) == len(hex_ids)
    assert set(cache.store) == {"8928308280fffff"}


def test_data_context_to_geojson_returns_feature_collection(monkeypatch: pytest.MonkeyPatch) -> None:
    context = DataContext(settings=UISettings())
    context.geometries = pd.DataFrame(
        {
            "hex_id": ["8928308280fffff"],
            "geometry": [
                json.dumps(
                    {
                        "type": "FeatureCollection",
                        "features": [],
                    }
                )
            ],
            "geometry_wkt": ["POLYGON((0 0,1 0,1 1,0 1,0 0))"],
            "centroid_lon": [0.5],
            "centroid_lat": [0.5],
            "resolution": [6],
        }
    )
    frame = pd.DataFrame({"hex_id": ["8928308280fffff"], "aucs": [75.0]})
    monkeypatch.setattr(
        "Urban_Amenities2.ui.data_loader.build_feature_collection",
        lambda *_args, **_kwargs: {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]]],
                    },
                    "properties": {"aucs": 75.0},
                }
            ],
        },
    )
    payload = context.to_geojson(frame)
    assert payload["type"] == "FeatureCollection"
    assert len(payload["features"]) == 1
    feature = payload["features"][0]
    assert feature["properties"]["aucs"] == 75.0


def test_data_context_builds_typed_overlays(monkeypatch: pytest.MonkeyPatch) -> None:
    context = DataContext(settings=UISettings())
    context.scores = pd.DataFrame(
        {
            "hex_id": ["8928308280fffff", "8928308280fffff"],
            "state": ["CO", "CO"],
        }
    )
    context.geometries = pd.DataFrame(
        {
            "hex_id": ["8928308280fffff"],
            "geometry_wkt": ["POLYGON((0 0,1 0,1 1,0 1,0 0))"],
            "geometry": [json.dumps({"type": "Polygon", "coordinates": []})],
            "centroid_lon": [0.5],
            "centroid_lat": [0.5],
            "resolution": [6],
        }
    )
    context._aggregation_version = "test"

    class _DummyShape:
        is_empty = False

        def simplify(self, *_args: object, **_kwargs: object) -> _DummyShape:
            return self

    class _DummyLoader:
        @staticmethod
        def loads(_wkt: str) -> _DummyShape:
            return _DummyShape()

    def _dummy_union(_shapes: list[_DummyShape]) -> _DummyShape:
        return _DummyShape()

    def _dummy_mapping(_shape: _DummyShape) -> dict[str, object]:
        return {
            "type": "Polygon",
            "coordinates": [[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]]],
        }

    monkeypatch.setattr("Urban_Amenities2.ui.data_loader.import_module", lambda name: {
        "shapely.wkt": _DummyLoader,
        "shapely.ops": type("_Ops", (), {"unary_union": staticmethod(_dummy_union)}),
        "shapely.geometry": type("_Geom", (), {"mapping": staticmethod(_dummy_mapping)}),
    }[name])

    context._build_overlays(force=True)
    payload = context.get_overlay("states")
    assert payload["type"] == "FeatureCollection"
    assert payload["features"]
    feature = payload["features"][0]
    assert feature["properties"]["label"] == "CO"


def test_data_context_summary_returns_expected_columns() -> None:
    context = DataContext(settings=UISettings())
    context.scores = pd.DataFrame(
        {
            "hex_id": ["a", "b", "c"],
            "aucs": [10.0, 20.0, 30.0],
        }
    )
    summary = context.summarise(["aucs"])
    assert "aucs" in summary.index
    assert {"min", "max", "mean"}.issubset(summary.columns)


def _write_dataset(
    base_path: Path,
    identifier: str,
    hex_ids: list[str],
    states: list[str],
    timestamp: datetime,
    *,
    nested: bool = False,
) -> None:
    scores = pd.DataFrame(
        {
            "hex_id": hex_ids,
            "aucs": [float(60 + index * 5) for index in range(len(hex_ids))],
            "EA": [float(50 + index) for index in range(len(hex_ids))],
            "LCA": [float(48 + index) for index in range(len(hex_ids))],
            "MUHAA": [float(47 + index) for index in range(len(hex_ids))],
            "JEA": [float(46 + index) for index in range(len(hex_ids))],
            "MORR": [float(45 + index) for index in range(len(hex_ids))],
            "CTE": [float(44 + index) for index in range(len(hex_ids))],
            "SOU": [float(43 + index) for index in range(len(hex_ids))],
        }
    )
    scores["hex_id"] = scores["hex_id"].astype(str)
    if nested:
        run_dir = base_path / identifier
        run_dir.mkdir(parents=True, exist_ok=True)
        scores_path = run_dir / "scores.parquet"
        metadata_path = run_dir / "metadata.parquet"
    else:
        scores_path = base_path / f"{identifier}_scores.parquet"
        metadata_path = base_path / f"{identifier}_metadata.parquet"
    scores.to_parquet(scores_path)
    metadata = pd.DataFrame(
        {
            "hex_id": hex_ids,
            "state": states,
            "metro": [f"Metro {identifier}"] * len(hex_ids),
            "county": [f"County {identifier}"] * len(hex_ids),
        }
    )
    metadata["hex_id"] = metadata["hex_id"].astype(str)
    metadata.to_parquet(metadata_path)
    epoch = timestamp.timestamp()
    os.utime(scores_path, (epoch, epoch))
    os.utime(metadata_path, (epoch, epoch))


def test_data_context_lists_versions_and_switches(
    tmp_path: Path, sample_hex_ids: list[str]
) -> None:
    data_path = tmp_path / "ui-data"
    data_path.mkdir()
    _write_dataset(
        data_path,
        "20240101",
        sample_hex_ids,
        ["CO", "NE", "CA"],
        datetime(2024, 1, 1, 12, 0, 0),
    )
    _write_dataset(
        data_path,
        "20240201",
        sample_hex_ids,
        ["WA", "OR", "CA"],
        datetime(2024, 2, 1, 12, 0, 0),
        nested=True,
    )

    settings = UISettings(data_path=data_path)
    context = DataContext.from_settings(settings)
    assert context.version is not None
    assert context.version.identifier == "20240201"
    assert context.scores.loc[0, "state"] == "WA"

    identifiers = [version.identifier for version in context.available_versions()]
    assert identifiers == ["20240201", "20240101"]

    assert context.load_version("20240101") is True
    assert context.version is not None
    assert context.version.identifier == "20240101"
    assert context.scores.loc[0, "state"] == "CO"


def test_data_context_prefers_version_specific_overlays(
    tmp_path: Path, sample_hex_ids: list[str]
) -> None:
    data_path = tmp_path / "ui-data"
    data_path.mkdir()
    _write_dataset(
        data_path,
        "20240101",
        sample_hex_ids,
        ["CO", "NE", "CA"],
        datetime(2024, 3, 1, 12, 0, 0),
        nested=True,
    )

    version_dir = data_path / "20240101"
    version_overlays = version_dir / "overlays"
    version_overlays.mkdir(parents=True, exist_ok=True)
    (version_overlays / "parks.geojson").write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[[-104.0, 39.7], [-104.0, 39.8], [-104.1, 39.8], [-104.1, 39.7], [-104.0, 39.7]]],
                        },
                        "properties": {"label": "Version parks"},
                    }
                ],
            }
        )
    )

    global_overlays = data_path / "overlays"
    global_overlays.mkdir(parents=True, exist_ok=True)
    (global_overlays / "parks.geojson").write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[[-105.0, 40.7], [-105.0, 40.8], [-105.1, 40.8], [-105.1, 40.7], [-105.0, 40.7]]],
                        },
                        "properties": {"label": "Global parks"},
                    }
                ],
            }
        )
    )

    settings = UISettings(data_path=data_path)
    context = DataContext.from_settings(settings)
    context.rebuild_overlays(force=True)
    parks = context.get_overlay("parks")
    assert parks["features"]
    assert parks["features"][0]["properties"]["label"] == "Version parks"
