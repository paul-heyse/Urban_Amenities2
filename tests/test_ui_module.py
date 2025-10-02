from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from Urban_Amenities2.ui.config import UISettings
from Urban_Amenities2.ui.data_loader import DataContext
from Urban_Amenities2.ui.hexes import HexGeometryCache, hex_centroid, hex_to_geojson


@pytest.fixture()
def sample_hexes() -> list[str]:
    h3 = pytest.importorskip("h3")
    return [
        h3.latlng_to_cell(39.7392, -104.9903, 9),
        h3.latlng_to_cell(40.7608, -111.8910, 9),
    ]


def test_geometry_cache(sample_hexes: list[str]) -> None:
    cache = HexGeometryCache()
    df = cache.ensure_geometries(sample_hexes)
    assert set(df["hex_id"]) == set(sample_hexes)
    for hex_id in sample_hexes:
        centroid = hex_centroid(hex_id)
        assert len(centroid) == 2
        geojson = hex_to_geojson(hex_id)
        assert geojson["type"] == "Polygon"
    cache.validate(sample_hexes)


def test_data_context_aggregation(tmp_path: Path, sample_hexes: list[str]) -> None:
    settings = UISettings()
    context = DataContext(settings=settings)
    scores = pd.DataFrame(
        {
            "hex_id": sample_hexes,
            "aucs": [80.0, 60.0],
            "EA": [75.0, 55.0],
            "state": ["CO", "UT"],
            "metro": ["Denver", "Salt Lake City"],
            "county": ["Denver County", "Salt Lake County"],
        }
    )
    context.scores = scores
    context.metadata = scores[["hex_id", "state", "metro", "county"]]
    context._prepare_geometries()
    context.validate_geometries()
    aggregated = context.aggregate_by_resolution(8, columns=["aucs", "EA"])
    assert {"hex_id", "aucs", "EA", "count"} <= set(aggregated.columns)
    geojson = context.to_geojson(scores)
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) == len(scores)
    export_path = tmp_path / "scores.geojson"
    context.export_geojson(export_path)
    payload = json.loads(export_path.read_text())
    assert payload["features"]
