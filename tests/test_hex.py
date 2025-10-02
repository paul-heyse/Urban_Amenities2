from __future__ import annotations

import pandas as pd
from shapely.geometry import LineString, Polygon

from Urban_Amenities2.hex.aggregation import (
    aggregate_by_hex,
    lines_to_hex,
    points_to_hex,
    polygons_to_hex,
)
from Urban_Amenities2.hex.core import hex_centroid, hex_distance_m, hex_neighbors, latlon_to_hex


def test_latlon_roundtrip() -> None:
    lat, lon = 39.7392, -104.9903
    hex_id = latlon_to_hex(lat, lon)
    centroid_lat, centroid_lon = hex_centroid(hex_id)
    assert abs(centroid_lat - lat) < 0.1
    assert abs(centroid_lon - lon) < 0.1


def test_hex_distance() -> None:
    lat, lon = 39.7392, -104.9903
    hex_a = latlon_to_hex(lat, lon)
    hex_b = next(iter(hex_neighbors(hex_a, 1)))
    distance = hex_distance_m(hex_a, hex_b)
    assert distance > 0


def test_points_to_hex() -> None:
    frame = pd.DataFrame({"lat": [39.7392, 39.74], "lon": [-104.99, -104.98]})
    result = points_to_hex(frame)
    assert "hex_id" in result
    assert len(result["hex_id"].unique()) <= len(result)


def test_lines_to_hex() -> None:
    line = LineString([(-105.0, 39.73), (-104.98, 39.74)])
    frame = pd.DataFrame({"geometry": [line]})
    result = lines_to_hex(frame)
    assert "hex_id" in result


def test_aggregate_by_hex() -> None:
    hex_id = latlon_to_hex(39.7392, -104.9903)
    frame = pd.DataFrame({"hex_id": [hex_id, hex_id], "value": [1, 2]})
    aggregated = aggregate_by_hex(frame, group_columns=["hex_id"], value_column="value")
    assert aggregated.loc[0, "value"] == 3


def test_polygons_to_hex() -> None:
    polygon = Polygon([(-105.0, 39.73), (-105.0, 39.74), (-104.99, 39.74), (-104.99, 39.73)])
    frame = pd.DataFrame({"geometry": [polygon], "value": [100]})
    result = polygons_to_hex(frame)
    assert not result.empty
    assert abs(result["value"].sum() - 100) < 1e-6
