"""Tests for UI export functionality."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest

from Urban_Amenities2.ui.export import (
    create_shareable_url,
    export_csv,
    export_geojson,
    export_parquet,
)


@pytest.fixture
def sample_data():
    """Create sample hex data for export testing."""
    return pd.DataFrame({
        "hex_id": ["8928308280fffff", "8928308281fffff"],
        "state": ["CO", "CO"],
        "metro": ["Denver", "Denver"],
        "aucs": [75.0, 45.0],
        "ea": [80.0, 50.0],
        "lca": [70.0, 40.0],
        "muhaa": [65.0, 35.0],
        "jea": [85.0, 55.0],
        "morr": [75.0, 45.0],
        "cte": [60.0, 30.0],
        "sou": [70.0, 40.0],
    })


def test_export_csv(sample_data):
    """Test CSV export."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "export.csv"
        export_csv(sample_data, output_path, include_geometry=True)

        # Verify file exists
        assert output_path.exists()

        # Load and verify content
        loaded = pd.read_csv(output_path)
        assert len(loaded) == len(sample_data)
        assert "hex_id" in loaded.columns
        assert "aucs" in loaded.columns
        assert "lat" in loaded.columns  # Added by include_geometry
        assert "lon" in loaded.columns


def test_export_geojson(sample_data):
    """Test GeoJSON export."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "export.geojson"
        export_geojson(sample_data, output_path)

        # Verify file exists
        assert output_path.exists()

        # Load and verify content
        gdf = gpd.read_file(output_path)
        assert len(gdf) == len(sample_data)
        assert "hex_id" in gdf.columns
        assert "aucs" in gdf.columns
        assert gdf.crs == "EPSG:4326"

        # Verify geometries are polygons
        assert all(gdf.geometry.type == "Polygon")


def test_export_geojson_with_properties(sample_data):
    """Test GeoJSON export with selected properties."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "export.geojson"
        export_geojson(sample_data, output_path, properties=["hex_id", "aucs", "ea"])

        # Load and verify only selected properties
        gdf = gpd.read_file(output_path)
        assert set(gdf.columns) == {"hex_id", "aucs", "ea", "geometry"}


def test_export_parquet(sample_data):
    """Test Parquet export."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "export.parquet"
        export_parquet(sample_data, output_path)

        # Verify file exists
        assert output_path.exists()

        # Load and verify content
        loaded = pd.read_parquet(output_path)
        pd.testing.assert_frame_equal(loaded, sample_data)


def test_create_shareable_url_basic():
    """Test creating basic shareable URL."""
    url = create_shareable_url("https://aucs.example.com")
    assert url == "https://aucs.example.com"


def test_create_shareable_url_with_filters():
    """Test creating shareable URL with filters."""
    url = create_shareable_url(
        "https://aucs.example.com",
        state="CO",
        metro="Denver",
        subscore="ea",
    )
    assert "https://aucs.example.com?" in url
    assert "state=CO" in url
    assert "metro=Denver" in url
    assert "subscore=ea" in url


def test_create_shareable_url_with_map_position():
    """Test creating shareable URL with map position."""
    url = create_shareable_url(
        "https://aucs.example.com",
        zoom=10,
        center_lat=39.7392,
        center_lon=-104.9903,
    )
    assert "zoom=10" in url
    assert "lat=39.7392" in url
    assert "lon=-104.9903" in url


def test_create_shareable_url_complete():
    """Test creating complete shareable URL with all parameters."""
    url = create_shareable_url(
        "https://aucs.example.com",
        state="CO",
        metro="Denver",
        subscore="lca",
        zoom=12,
        center_lat=39.7392,
        center_lon=-104.9903,
    )

    # Verify all parameters present
    assert "state=CO" in url
    assert "metro=Denver" in url
    assert "subscore=lca" in url
    assert "zoom=12" in url
    assert "lat=39.7392" in url
    assert "lon=-104.9903" in url

