from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import geopandas as gpd
import pandas as pd

from ...hex.aggregation import points_to_hex
from ...logging_utils import get_logger

LOGGER = get_logger("aucs.ingest.parks.padus")


def load_padus(path: str | Path) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(path)
    return gdf


def filter_padus(gdf: gpd.GeoDataFrame, states: Iterable[str]) -> gpd.GeoDataFrame:
    states = {state.upper() for state in states}
    if "Access" in gdf.columns:
        filtered = gdf[gdf["Access"].str.lower() == "open"].copy()
    else:
        filtered = gdf.copy()
    if "State" in filtered.columns:
        filtered = filtered[filtered["State"].str.upper().isin(states)]
    return filtered


def compute_access_points(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf = gdf.copy()
    gdf["access_point"] = gdf.geometry.centroid
    return gdf


def index_to_hex(gdf: gpd.GeoDataFrame) -> pd.DataFrame:
    gdf = compute_access_points(gdf)
    frame = pd.DataFrame(
        {
            "name": gdf.get("Unit_Name", gdf.get("NAME", "")),
            "hex_id": points_to_hex(
                pd.DataFrame({"lat": gdf.access_point.y, "lon": gdf.access_point.x}),
                lat_column="lat",
                lon_column="lon",
                hex_column="hex_id",
            )["hex_id"],
            "geometry": gdf.access_point,
        }
    )
    return frame


def ingest_padus(
    path: str | Path,
    states: Iterable[str],
    output_path: Path = Path("data/processed/parks.parquet"),
) -> pd.DataFrame:
    gdf = load_padus(path)
    filtered = filter_padus(gdf, states)
    indexed = index_to_hex(filtered)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    indexed.to_parquet(output_path)
    return indexed


__all__ = ["load_padus", "filter_padus", "compute_access_points", "index_to_hex", "ingest_padus"]
