from __future__ import annotations

import json

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
