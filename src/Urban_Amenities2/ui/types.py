"""Shared typing helpers for UI data loading and overlays."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal, TypeAlias, TypedDict

Bounds: TypeAlias = tuple[float, float, float, float]
AggregationCacheKey: TypeAlias = tuple[int, tuple[str, ...]]


class AmenityEntry(TypedDict, total=False):
    """Top amenity metadata surfaced for a selected hex."""

    name: str
    category: str
    score: float


ModeShareMap: TypeAlias = dict[str, float]


class ScoreRecord(TypedDict, total=False):
    """Core score row exported from the aggregation pipeline."""

    hex_id: str
    aucs: float
    EA: float
    LCA: float
    MUHAA: float
    JEA: float
    MORR: float
    CTE: float
    SOU: float
    ea: float
    lca: float
    muhaa: float
    jea: float
    morr: float
    cte: float
    sou: float
    lat: float
    lon: float
    centroid_lat: float
    centroid_lon: float
    population: float | None
    state: str
    metro: str | None
    county: str | None
    top_amenities: list[AmenityEntry]
    top_modes: ModeShareMap


class MetadataRecord(TypedDict, total=False):
    """Supplementary metadata joined onto scores."""

    hex_id: str
    state: str
    metro: str | None
    county: str | None


class SummaryRow(TypedDict, total=False):
    """Aggregate statistics reported in the UI summary tables."""

    min: float
    max: float
    mean: float
    p5: float
    p25: float
    p50: float
    p75: float
    p95: float


class GeoJSONGeometry(TypedDict, total=False):
    """Generic GeoJSON geometry container."""

    type: str
    coordinates: object
    geometries: list[GeoJSONGeometry]


class GeoJSONFeature(TypedDict):
    """Generic GeoJSON Feature container."""

    type: Literal["Feature"]
    geometry: GeoJSONGeometry
    properties: dict[str, object]


class OverlayProperties(TypedDict, total=False):
    """Properties emitted for overlay feature metadata."""

    label: str


class OverlayFeature(GeoJSONFeature):
    """Overlay-specific GeoJSON feature payload."""

    properties: OverlayProperties


class FeatureCollection(TypedDict):
    """GeoJSON FeatureCollection payload."""

    type: Literal["FeatureCollection"]
    features: list[GeoJSONFeature]


OverlayMap: TypeAlias = dict[str, FeatureCollection]


@dataclass(slots=True)
class GeometryCacheEntry:
    """Record persisted in the hex geometry cache."""

    hex_id: str
    geometry: str
    geometry_wkt: str
    centroid_lon: float
    centroid_lat: float
    resolution: int

    def as_record(self) -> dict[str, object]:
        return {
            "hex_id": self.hex_id,
            "geometry": self.geometry,
            "geometry_wkt": self.geometry_wkt,
            "centroid_lon": self.centroid_lon,
            "centroid_lat": self.centroid_lat,
            "resolution": self.resolution,
        }


def empty_feature_collection() -> FeatureCollection:
    """Return a typed empty FeatureCollection payload."""

    return {"type": "FeatureCollection", "features": []}


OVERLAY_NAMES: Final[tuple[str, ...]] = (
    "states",
    "counties",
    "metros",
    "transit_lines",
    "transit_stops",
    "parks",
)


__all__ = [
    "AggregationCacheKey",
    "AmenityEntry",
    "Bounds",
    "FeatureCollection",
    "GeoJSONFeature",
    "GeoJSONGeometry",
    "GeometryCacheEntry",
    "ModeShareMap",
    "MetadataRecord",
    "OverlayFeature",
    "OverlayMap",
    "OverlayProperties",
    "OVERLAY_NAMES",
    "ScoreRecord",
    "SummaryRow",
    "empty_feature_collection",
]
