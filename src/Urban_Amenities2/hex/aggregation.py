"""Spatial aggregation helpers built on top of H3."""
from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd
from shapely.geometry import LineString, Polygon

from .core import RESOLUTION, hex_boundary, hex_neighbors, latlon_to_hex


def points_to_hex(
    frame: pd.DataFrame,
    lat_column: str = "lat",
    lon_column: str = "lon",
    hex_column: str = "hex_id",
    resolution: int = RESOLUTION,
) -> pd.DataFrame:
    """Assign a hex_id to each point feature using vectorised operations."""

    lats = frame[lat_column].to_numpy(dtype=float)
    lons = frame[lon_column].to_numpy(dtype=float)
    vectorised = np.vectorize(lambda lat, lon: latlon_to_hex(lat, lon, resolution))
    hexes = vectorised(lats, lons)
    frame = frame.copy()
    frame[hex_column] = hexes
    return frame


def lines_to_hex(
    frame: pd.DataFrame,
    geometry_column: str = "geometry",
    hex_column: str = "hex_id",
    resolution: int = RESOLUTION,
) -> pd.DataFrame:
    """Assign line features to hexagons using midpoint sampling."""

    def _line_to_hex(line: LineString) -> str:
        if not isinstance(line, LineString):
            raise TypeError("Line geometry must be a shapely LineString")
        midpoint = line.interpolate(0.5, normalized=True)
        return latlon_to_hex(midpoint.y, midpoint.x, resolution)

    frame = frame.copy()
    frame[hex_column] = frame[geometry_column].map(_line_to_hex)
    return frame


def polygons_to_hex(
    frame: pd.DataFrame,
    geometry_column: str = "geometry",
    hex_column: str = "hex_id",
    value_column: str = "value",
    resolution: int = RESOLUTION,
) -> pd.DataFrame:
    """Explode polygons into hexagons with area weighted values."""

    records: list[dict[str, object]] = []
    for _, row in frame.iterrows():
        polygon = row[geometry_column]
        if not isinstance(polygon, Polygon):
            raise TypeError("Polygon geometry must be a shapely Polygon")
        total_area = polygon.area
        if total_area <= 0:
            continue
        centroid = polygon.centroid
        queue = {latlon_to_hex(float(centroid.y), float(centroid.x), resolution)}
        visited: set[str] = set()
        while queue:
            hex_id = queue.pop()
            if hex_id in visited:
                continue
            visited.add(hex_id)
            boundary_polygon = Polygon([(lon, lat) for lat, lon in hex_boundary(hex_id)])
            intersection = boundary_polygon.intersection(polygon)
            if intersection.is_empty:
                continue
            weight = intersection.area / total_area
            record = row.to_dict()
            record[hex_column] = hex_id
            record[value_column] = float(row[value_column]) * weight
            records.append(record)
            for neighbor in hex_neighbors(hex_id, 1):
                queue.add(neighbor)
    return pd.DataFrame.from_records(records)


def aggregate_by_hex(
    frame: pd.DataFrame,
    group_columns: Iterable[str],
    value_column: str,
    agg: str = "sum",
) -> pd.DataFrame:
    """Aggregate values by hex and optional additional columns."""

    grouped = frame.groupby(list(group_columns))[value_column].agg(agg)
    return grouped.reset_index()
