"""Factories for typed UI test datasets."""

from __future__ import annotations

import json
import os
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

import pandas as pd

from Urban_Amenities2.ui.config import UISettings


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


def make_ui_settings(data_path: Path) -> UISettings:
    """Construct UI settings backed by a deterministic dataset path."""

    return UISettings(
        host="127.0.0.1",
        port=8060,
        debug=False,
        secret_key="test",
        mapbox_token=None,
        cors_origins=["https://example.com"],
        enable_cors=True,
        data_path=data_path,
        log_level="DEBUG",
        title="Test Amenities Explorer",
        reload_interval_seconds=30,
        hex_resolutions=[7, 8, 9],
        summary_percentiles=[5, 50, 95],
    )


def write_ui_dataset(
    base_path: Path,
    identifier: str,
    hex_ids: Sequence[str],
    states: Sequence[str],
    timestamp: datetime,
    *,
    nested: bool = False,
) -> None:
    """Materialise parquet score and metadata files for UI regression tests."""

    scores = pd.DataFrame(
        {
            "hex_id": list(hex_ids),
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
            "hex_id": list(hex_ids),
            "state": list(states),
            "metro": [f"Metro {identifier}"] * len(hex_ids),
            "county": [f"County {identifier}"] * len(hex_ids),
        }
    )
    metadata["hex_id"] = metadata["hex_id"].astype(str)
    metadata.to_parquet(metadata_path)

    epoch = timestamp.timestamp()
    scores_path.touch()
    os.utime(scores_path, (epoch, epoch))
    os.utime(metadata_path, (epoch, epoch))


def write_overlay_file(base: Path, name: str, label: str) -> Path:
    """Create a simple GeoJSON overlay for regression tests."""

    base.mkdir(parents=True, exist_ok=True)
    payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [-104.0, 39.7],
                            [-104.0, 39.8],
                            [-104.1, 39.8],
                            [-104.1, 39.7],
                            [-104.0, 39.7],
                        ]
                    ],
                },
                "properties": {"label": label},
            }
        ],
    }
    path = base / f"{name}.geojson"
    path.write_text(json.dumps(payload))
    return path


__all__ = [
    "make_export_dataset",
    "make_filter_dataset",
    "make_ui_settings",
    "write_overlay_file",
    "write_ui_dataset",
]
