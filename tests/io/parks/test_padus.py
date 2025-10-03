from __future__ import annotations

from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Polygon

from Urban_Amenities2.io.parks import padus


@pytest.fixture(autouse=True)
def patch_points_to_hex(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_points_to_hex(frame: pd.DataFrame, **_: Any) -> pd.DataFrame:
        frame = frame.copy()
        frame["hex_id"] = [f"hex-{idx}" for idx in range(len(frame))]
        return frame

    monkeypatch.setattr(padus, "points_to_hex", _fake_points_to_hex)


def _sample_gdf() -> gpd.GeoDataFrame:
    polygon = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    return gpd.GeoDataFrame({"Unit_Name": ["Park"], "State": ["CO"], "Access": ["Open"], "geometry": [polygon]})


def test_filter_padus_limits_to_states() -> None:
    gdf = _sample_gdf()
    filtered = padus.filter_padus(gdf, states=["co"])
    assert len(filtered) == 1
    assert filtered.iloc[0]["Unit_Name"] == "Park"


def test_compute_access_points_uses_centroid() -> None:
    gdf = _sample_gdf()
    with_centroids = padus.compute_access_points(gdf)
    assert with_centroids.iloc[0]["access_point"].x == pytest.approx(0.5)


def test_index_to_hex_returns_dataframe() -> None:
    gdf = _sample_gdf()
    indexed = padus.index_to_hex(gdf)
    assert set(indexed.columns) == {"name", "hex_id", "geometry"}
    assert indexed.loc[0, "name"] == "Park"


def test_ingest_padus_writes_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    gdf = _sample_gdf()
    monkeypatch.setattr(padus, "load_padus", lambda path: gdf)
    monkeypatch.setattr(
        padus,
        "index_to_hex",
        lambda frame: pd.DataFrame({"name": ["Park"], "hex_id": ["hex-0"], "geometry": [None]}),
    )
    output = tmp_path / "parks.parquet"
    result = padus.ingest_padus(Path("padus.gpkg"), states=["CO"], output_path=output)
    assert output.exists()
    assert not result.empty
