"""Factories for typed UI test datasets."""

from __future__ import annotations

import pandas as pd


def make_filter_dataset() -> pd.DataFrame:
    """Create a deterministic dataset for filter-related tests."""

    data = {
        "hex_id": [
            "8928308280fffff",
            "8928308281fffff",
            "8928308282fffff",
            "8928308283fffff",
            "8928308284fffff",
        ],
        "state": ["CO", "CO", "UT", "ID", "ID"],
        "metro": ["Denver", "Denver", "Salt Lake City", "Boise", "Boise"],
        "county": ["Denver", "Denver", "Salt Lake", "Ada", "Jefferson"],
        "aucs": [75.0, 45.0, 60.0, 30.0, 40.0],
        "pop_density": [5000.0, 2000.0, 3000.0, 500.0, 1200.0],
        "land_use": ["urban", "suburban", "urban", "rural", "suburban"],
        "lat": [39.7, 39.8, 40.7, 43.6, 43.7],
        "lon": [-104.9, -104.8, -111.8, -116.2, -116.1],
    }
    return pd.DataFrame(data)


def make_export_dataset() -> pd.DataFrame:
    """Dataset for export-related tests including required columns."""

    data = {
        "hex_id": ["8928308280fffff", "8928308280bffff"],
        "state": ["CO", "CO"],
        "metro": ["Denver", "Denver"],
        "county": ["Denver", "Denver"],
        "aucs": [75.0, 45.0],
        "ea": [80.0, 50.0],
        "lca": [70.0, 40.0],
        "muhaa": [65.0, 35.0],
        "jea": [85.0, 55.0],
        "morr": [75.0, 45.0],
        "cte": [60.0, 30.0],
        "sou": [70.0, 40.0],
    }
    frame = pd.DataFrame(data)
    frame["hex_id"] = frame["hex_id"].astype(str)
    return frame


__all__ = ["make_filter_dataset", "make_export_dataset"]
