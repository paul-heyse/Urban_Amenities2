"""Tests for UI filtering functionality."""

from __future__ import annotations

import pandas as pd
import pytest

from Urban_Amenities2.ui.filters import FilterConfig, apply_filters, get_filter_options


@pytest.fixture
def sample_data():
    """Create sample hex data for testing."""
    return pd.DataFrame({
        "hex_id": ["8928308280fffff", "8928308281fffff", "8928308282fffff", "8928308283fffff"],
        "state": ["CO", "CO", "UT", "ID"],
        "metro": ["Denver", "Denver", "Salt Lake City", "Boise"],
        "aucs": [75.0, 45.0, 60.0, 30.0],
        "pop_density": [5000, 2000, 3000, 500],
        "land_use": ["urban", "suburban", "urban", "rural"],
        "lat": [39.7, 39.8, 40.7, 43.6],
        "lon": [-104.9, -104.8, -111.8, -116.2],
    })


def test_filter_by_state(sample_data):
    """Test filtering by state."""
    config = FilterConfig(state=["CO"])
    filtered = apply_filters(sample_data, config)
    assert len(filtered) == 2
    assert all(filtered["state"] == "CO")


def test_filter_by_metro(sample_data):
    """Test filtering by metro area."""
    config = FilterConfig(metro=["Denver"])
    filtered = apply_filters(sample_data, config)
    assert len(filtered) == 2
    assert all(filtered["metro"] == "Denver")


def test_filter_by_score_range(sample_data):
    """Test filtering by score range."""
    config = FilterConfig(score_min=50.0, score_max=80.0)
    filtered = apply_filters(sample_data, config)
    assert len(filtered) == 2
    assert all((filtered["aucs"] >= 50.0) & (filtered["aucs"] <= 80.0))


def test_filter_by_population_density(sample_data):
    """Test filtering by population density."""
    config = FilterConfig(population_density_min=2000, population_density_max=5000)
    filtered = apply_filters(sample_data, config)
    assert len(filtered) == 3


def test_filter_by_land_use(sample_data):
    """Test filtering by land use."""
    config = FilterConfig(land_use=["urban"])
    filtered = apply_filters(sample_data, config)
    assert len(filtered) == 2
    assert all(filtered["land_use"] == "urban")


def test_combined_filters(sample_data):
    """Test multiple filters applied together."""
    config = FilterConfig(
        state=["CO", "UT"],
        score_min=50.0,
        land_use=["urban"],
    )
    filtered = apply_filters(sample_data, config)
    assert len(filtered) == 2  # Denver (75) and Salt Lake City (60)


def test_get_filter_options(sample_data):
    """Test extracting available filter options."""
    options = get_filter_options(sample_data)

    assert set(options["states"]) == {"CO", "ID", "UT"}
    assert set(options["metros"]) == {"Boise", "Denver", "Salt Lake City"}
    assert options["score_range"] == [30.0, 75.0]
    assert set(options["land_uses"]) == {"rural", "suburban", "urban"}
    assert options["population_density_range"] == [500, 5000]


def test_empty_filter_returns_all(sample_data):
    """Test that empty filter returns all data."""
    config = FilterConfig()
    filtered = apply_filters(sample_data, config)
    assert len(filtered) == len(sample_data)
    pd.testing.assert_frame_equal(filtered, sample_data)


def test_filter_resulting_in_no_data(sample_data):
    """Test filter that excludes all data."""
    config = FilterConfig(score_min=100.0)
    filtered = apply_filters(sample_data, config)
    assert len(filtered) == 0

