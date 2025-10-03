from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString

from ...hex.aggregation import points_to_hex
from ...logging_utils import get_logger

LOGGER = get_logger("aucs.ingest.parks.trails")


def load_trails(path: str | Path) -> gpd.GeoDataFrame:
    return gpd.read_file(path)


def sample_line(line: LineString, samples: int = 5) -> list[tuple[float, float]]:
    if samples <= 1:
        midpoint = line.interpolate(0.5, normalized=True)
        return [(midpoint.y, midpoint.x)]
    return [
        (point.y, point.x)
        for point in (line.interpolate(i / (samples - 1), normalized=True) for i in range(samples))
    ]


def index_trails(gdf: gpd.GeoDataFrame, samples: int = 5) -> pd.DataFrame:
    records = []
    for _, row in gdf.iterrows():
        geometry = row.geometry
        if not isinstance(geometry, LineString):
            continue
        for lat, lon in sample_line(geometry, samples=samples):
            records.append({"trail_id": row.get("TRAIL_ID", row.get("id")), "lat": lat, "lon": lon})
    frame = pd.DataFrame.from_records(records)
    if frame.empty:
        return frame.assign(hex_id=[])
    frame = points_to_hex(frame, lat_column="lat", lon_column="lon", hex_column="hex_id")
    return frame


def ingest_trails(
    path: str | Path, output_path: Path = Path("data/processed/trails.parquet")
) -> pd.DataFrame:
    gdf = load_trails(path)
    indexed = index_trails(gdf)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    indexed.to_parquet(output_path)
    return indexed


__all__ = ["load_trails", "index_trails", "ingest_trails"]
