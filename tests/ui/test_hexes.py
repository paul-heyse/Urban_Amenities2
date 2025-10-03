from __future__ import annotations

import pandas as pd
import pytest

from Urban_Amenities2.ui import hexes


@pytest.mark.usefixtures("fake_h3")
def test_hex_geometry_helpers_cache(fake_h3) -> None:
    hex_id = "abc123"
    feature = hexes.hex_to_geojson(hex_id)
    assert feature["type"] == "Polygon"
    assert len(feature["coordinates"][0]) == 5  # closed ring

    assert fake_h3.boundary_calls.count(hex_id) == 1

    # Cached calls should not trigger additional boundary lookups for the same helper.
    hexes.hex_to_geojson(hex_id)
    assert fake_h3.boundary_calls.count(hex_id) == 1

    hexes.hex_to_wkt(hex_id)
    assert fake_h3.boundary_calls.count(hex_id) == 2

    _ = hexes.hex_centroid(hex_id)


@pytest.mark.usefixtures("fake_h3")
def test_hex_geometry_cache_and_validation(fake_h3) -> None:
    cache = hexes.HexGeometryCache()
    ids = ["abc123", "def456"]
    frame = cache.ensure_geometries(ids)
    assert set(frame.columns) >= {
        "hex_id",
        "geometry",
        "geometry_wkt",
        "centroid_lon",
        "centroid_lat",
        "resolution",
    }
    assert len(frame) == 2

    # Second call uses cached values.
    initial_calls = fake_h3.boundary_calls.count("abc123")
    cache.ensure_geometries(ids)
    assert fake_h3.boundary_calls.count("abc123") == initial_calls

    cache.validate(ids)
    with pytest.raises(ValueError):
        cache.validate(["missing"])


@pytest.mark.usefixtures("fake_h3")
def test_build_hex_index(fake_h3) -> None:
    geometries = pd.DataFrame(
        {
            "hex_id": ["abc123", "def456", "ghi789"],
            "resolution": [9, 9, 9],
        }
    )
    index = hexes.build_hex_index(geometries, resolution=8)
    assert index
    for parent, children in index.items():
        assert parent.endswith("_r8")
        assert all(child in geometries["hex_id"].values for child in children)


@pytest.mark.usefixtures("fake_h3")
def test_hex_spatial_index_bbox_fallback(fake_h3) -> None:
    cache = hexes.HexGeometryCache()
    frame = cache.ensure_geometries(["abc123", "def456"])
    index = hexes.HexSpatialIndex(frame)
    index._tree = None
    index._box = None
    lon_min = float(frame["centroid_lon"].min()) - 0.001
    lat_min = float(frame["centroid_lat"].min()) - 0.001
    lon_max = float(frame["centroid_lon"].max()) + 0.001
    lat_max = float(frame["centroid_lat"].max()) + 0.001
    matches = index.query_bbox(lon_min, lat_min, lon_max, lat_max)
    assert set(matches) == set(frame["hex_id"].astype(str))

    neighbours = index.neighbours("abc123", k=1)
    assert "abc123" in neighbours
