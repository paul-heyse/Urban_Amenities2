"""Utilities for working with H3 hexagon geometries within the UI."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Dict, Iterable, List, Mapping, Sequence
import pandas as pd

from ..logging_utils import get_logger

LOGGER = get_logger("ui.hexes")


@lru_cache(maxsize=10_000)
def _hex_boundary_geojson(hex_id: str) -> str:
    h3 = __import__("h3")
    boundary = h3.cell_to_boundary(hex_id)
    coordinates = [(lon, lat) for lat, lon in boundary]
    if coordinates and coordinates[0] != coordinates[-1]:
        coordinates.append(coordinates[0])
    return json.dumps({"type": "Polygon", "coordinates": [coordinates]})


@lru_cache(maxsize=10_000)
def _hex_boundary_wkt(hex_id: str) -> str:
    h3 = __import__("h3")
    boundary = h3.cell_to_boundary(hex_id)
    coordinates = [(lon, lat) for lat, lon in boundary]
    if coordinates and coordinates[0] != coordinates[-1]:
        coordinates.append(coordinates[0])
    coords = ",".join(f"{lon} {lat}" for lon, lat in coordinates)
    return f"POLYGON(({coords}))"


@lru_cache(maxsize=10_000)
def _hex_centroid(hex_id: str) -> tuple[float, float]:
    h3 = __import__("h3")
    lat, lon = h3.cell_to_latlng(hex_id)
    return lon, lat


def hex_to_geojson(hex_id: str) -> dict:
    return json.loads(_hex_boundary_geojson(hex_id))


def hex_to_wkt(hex_id: str) -> str:
    return _hex_boundary_wkt(hex_id)


def hex_centroid(hex_id: str) -> tuple[float, float]:
    return _hex_centroid(hex_id)


@dataclass(slots=True)
class HexGeometryCache:
    """Cache hexagon geometries and derived attributes."""

    store: Dict[str, Dict[str, object]] = field(default_factory=dict)

    def ensure_geometries(self, hex_ids: Sequence[str]) -> pd.DataFrame:
        records = []
        for hex_id in hex_ids:
            if hex_id not in self.store:
                geometry = _hex_boundary_geojson(hex_id)
                wkt = _hex_boundary_wkt(hex_id)
                lon, lat = _hex_centroid(hex_id)
                resolution = __import__("h3").get_resolution(hex_id)
                self.store[hex_id] = {
                    "hex_id": hex_id,
                    "geometry": geometry,
                    "geometry_wkt": wkt,
                    "centroid_lon": lon,
                    "centroid_lat": lat,
                    "resolution": resolution,
                }
            records.append(self.store[hex_id])
        return pd.DataFrame.from_records(records)

    def validate(self, hex_ids: Sequence[str]) -> None:
        missing = [hex_id for hex_id in hex_ids if hex_id not in self.store]
        if missing:
            msg = f"Missing geometries for {len(missing)} hexes"
            raise ValueError(msg)


def build_hex_index(geometries: pd.DataFrame, resolution: int) -> Mapping[str, List[str]]:
    """Aggregate fine geometries into coarser resolution buckets."""

    h3 = __import__("h3")
    if geometries.empty:
        return {}
    _require_columns = {"hex_id"}
    if not _require_columns.issubset(geometries.columns):
        raise KeyError("Geometries frame must contain hex_id column")
    coarse_map: Dict[str, List[str]] = {}
    if "resolution" in geometries.columns:
        geoms = geometries[geometries["resolution"].astype(int) >= int(resolution)]
    else:
        geoms = geometries
    resolution_series = geoms.get("resolution")
    if resolution_series is None:
        iterator = ((hex_id, None) for hex_id in geoms["hex_id"].astype(str))
    else:
        iterator = zip(
            geoms["hex_id"].astype(str),
            resolution_series.astype(int),
            strict=False,
        )
    for hex_id, cell_resolution in iterator:
        if cell_resolution is not None and cell_resolution < int(resolution):
            continue
        parent = h3.cell_to_parent(hex_id, resolution)
        coarse_map.setdefault(parent, []).append(hex_id)
    return coarse_map


@dataclass(slots=True)
class HexSpatialIndex:
    """Spatial index leveraging shapely STRtree when available."""

    geometries: pd.DataFrame

    def __post_init__(self) -> None:
        try:
            from shapely import wkt as shapely_wkt
            from shapely.geometry import box
            from shapely.strtree import STRtree
        except ImportError:  # pragma: no cover - optional dependency
            self._tree = None
            LOGGER.warning("shapely_missing", msg="Shapely not installed; viewport queries use bbox fallback")
            return
        geometries = [shapely_wkt.loads(wkt) for wkt in self.geometries["geometry_wkt"]]
        self._tree = STRtree(geometries)
        self._geom_map = dict(zip(geometries, self.geometries["hex_id"]))
        self._box = box

    def query_bbox(self, lon_min: float, lat_min: float, lon_max: float, lat_max: float) -> List[str]:
        if getattr(self, "_tree", None) is None:
            frame = self.geometries
            mask = (
                (frame["centroid_lon"] >= lon_min)
                & (frame["centroid_lon"] <= lon_max)
                & (frame["centroid_lat"] >= lat_min)
                & (frame["centroid_lat"] <= lat_max)
            )
            return frame.loc[mask, "hex_id"].astype(str).tolist()
        envelope = self._box(lon_min, lat_min, lon_max, lat_max)
        matches = self._tree.query(envelope)
        return [self._geom_map[geom] for geom in matches]

    def neighbours(self, hex_id: str, k: int = 1) -> List[str]:
        h3 = __import__("h3")
        neighbours = h3.grid_disk(hex_id, k)
        return [cell for cell in neighbours if cell in self.geometries["hex_id"].values]


__all__ = [
    "HexGeometryCache",
    "HexSpatialIndex",
    "build_hex_index",
    "hex_to_geojson",
    "hex_to_wkt",
    "hex_centroid",
]
