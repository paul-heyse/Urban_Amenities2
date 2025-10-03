from __future__ import annotations

from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import LineString

from Urban_Amenities2.io.parks import trails


@pytest.fixture(autouse=True)
def patch_points_to_hex(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_points_to_hex(frame: pd.DataFrame, **_: Any) -> pd.DataFrame:
        frame = frame.copy()
        frame["hex_id"] = [f"hex-{idx}" for idx in range(len(frame))]
        return frame

    monkeypatch.setattr(trails, "points_to_hex", _fake_points_to_hex)


def test_sample_line_respects_sample_count() -> None:
    line = LineString([(0, 0), (0, 3)])
    samples = trails.sample_line(line, samples=3)
    assert len(samples) == 3
    assert samples[1] == (1.5, 0.0)


def test_index_trails_skips_non_linestring() -> None:
    gdf = gpd.GeoDataFrame({"geometry": [LineString([(0, 0), (0, 1)]), 5]})
    indexed = trails.index_trails(gdf, samples=2)
    assert all(value.startswith("hex-") for value in indexed["hex_id"])


def test_ingest_trails_writes_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    gdf = gpd.GeoDataFrame({"geometry": [LineString([(0, 0), (1, 1)])]})
    monkeypatch.setattr(trails, "load_trails", lambda path: gdf)
    output = tmp_path / "trails.parquet"
    result = trails.ingest_trails(Path("trails.gpkg"), output_path=output)
    assert output.exists()
    assert not result.empty
