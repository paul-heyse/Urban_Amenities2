from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from Urban_Amenities2.ui.components.choropleth import create_choropleth
from Urban_Amenities2.ui.config import UISettings
from Urban_Amenities2.ui.data_loader import DataContext
from Urban_Amenities2.ui.hexes import HexGeometryCache, hex_centroid, hex_to_geojson
from Urban_Amenities2.ui.layers import build_overlay_payload


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
    context._record_base_resolution()
    aggregated = context.aggregate_by_resolution(8, columns=["aucs", "EA"])
    assert {"hex_id", "aucs", "EA", "count"} <= set(aggregated.columns)
    geojson = context.to_geojson(scores)
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) == len(scores)
    export_path = tmp_path / "scores.geojson"
    context.export_geojson(export_path)
    payload = json.loads(export_path.read_text())
    assert payload["features"]


def test_viewport_selection(sample_hexes: list[str]) -> None:
    settings = UISettings()
    context = DataContext(settings=settings)
    scores = pd.DataFrame(
        {
            "hex_id": sample_hexes,
            "aucs": [82.0, 61.0],
            "EA": [70.0, 58.0],
            "state": ["CO", "UT"],
            "metro": ["Denver", "Salt Lake City"],
            "county": ["Denver County", "Salt Lake County"],
        }
    )
    context.scores = scores
    context.metadata = scores[["hex_id", "state", "metro", "county"]]
    context._prepare_geometries()
    context.validate_geometries()
    context._record_base_resolution()
    assert context.bounds is not None
    geometries = context.geometries.set_index("hex_id")
    lon = float(geometries.loc[sample_hexes[0], "centroid_lon"])
    lat = float(geometries.loc[sample_hexes[0], "centroid_lat"])
    bounds = (lon - 0.05, lat - 0.05, lon + 0.05, lat + 0.05)
    visible = context.ids_in_viewport(bounds, resolution=context.base_resolution)
    assert sample_hexes[0] in visible
    assert sample_hexes[1] not in visible
    frame = context.frame_for_resolution(context.base_resolution, columns=["aucs", "EA"])
    trimmed = context.apply_viewport(frame, context.base_resolution, bounds)
    assert len(trimmed) <= len(frame)
    assert trimmed["hex_id"].tolist() == [sample_hexes[0]]
    cached = context.frame_for_resolution(8, columns=["aucs"])
    cached.loc[:, "aucs"] = 0.0
    fresh = context.frame_for_resolution(8, columns=["aucs"])
    assert not (fresh["aucs"] == 0.0).all()


def test_overlay_payload_and_choropleth(sample_hexes: list[str]) -> None:
    pytest.importorskip("shapely")
    settings = UISettings()
    context = DataContext(settings=settings)
    scores = pd.DataFrame(
        {
            "hex_id": sample_hexes,
            "aucs": [82.0, 61.0],
            "EA": [70.0, 58.0],
            "state": ["CO", "UT"],
            "metro": ["Denver", "Salt Lake City"],
            "county": ["Denver County", "Salt Lake County"],
        }
    )
    context.scores = scores
    context.metadata = scores[["hex_id", "state", "metro", "county"]]
    context._prepare_geometries()
    context.validate_geometries()
    context._record_base_resolution()
    context.rebuild_overlays(force=True)
    context.overlays["transit_stops"] = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [-104.99, 39.74]},
                "properties": {"label": "Union Station"},
            }
        ],
    }
    payload = build_overlay_payload(
        ["states", "transit_stops", "city_labels"], context, opacity=0.5
    )
    assert payload.layers
    assert any(trace.name == "City labels" for trace in payload.traces)
    assert payload.traces
    frame = context.attach_geometries(scores)
    figure = create_choropleth(
        geojson=context.to_geojson(frame),
        frame=frame,
        score_column="aucs",
        hover_columns=["state"],
        mapbox_token=None,
        map_style="mapbox://styles/mapbox/streets-v11",
        layers=payload.layers,
        extra_traces=payload.traces,
        attribution="© Test",
    )
    assert figure.layout.mapbox.style == "open-street-map"
    assert figure.layout.annotations[0].text == "© Test"
