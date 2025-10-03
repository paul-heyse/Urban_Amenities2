"""Core utilities for working with H3 hexagons."""
from __future__ import annotations

from collections.abc import Iterable
from functools import lru_cache

import h3

RESOLUTION = 9


def latlon_to_hex(lat: float, lon: float, resolution: int = RESOLUTION) -> str:
    """Convert latitude/longitude to an H3 cell identifier."""

    return h3.latlng_to_cell(lat, lon, resolution)


@lru_cache(maxsize=65536)
def hex_centroid(hex_id: str) -> tuple[float, float]:
    """Return the centroid latitude/longitude for a given cell."""

    lat, lon = h3.cell_to_latlng(hex_id)
    return float(lat), float(lon)


@lru_cache(maxsize=65536)
def hex_boundary(hex_id: str) -> list[tuple[float, float]]:
    """Return the ordered boundary coordinates for a hexagon."""

    boundary = h3.cell_to_boundary(hex_id)
    return [(float(lat), float(lon)) for lat, lon in boundary]


def hex_distance_m(hex_a: str, hex_b: str) -> float:
    """Compute the great-circle distance between two hexagon centroids in metres."""

    lat_a, lon_a = hex_centroid(hex_a)
    lat_b, lon_b = hex_centroid(hex_b)
    return float(h3.great_circle_distance((lat_a, lon_a), (lat_b, lon_b), unit="m"))


def hex_neighbors(hex_id: str, k: int = 1) -> Iterable[str]:
    """Yield the k-ring neighbours for a hex cell."""

    for neighbor in h3.grid_disk(hex_id, k):
        if neighbor != hex_id:
            yield neighbor
