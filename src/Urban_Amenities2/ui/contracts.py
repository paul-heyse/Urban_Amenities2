"""Typed interfaces shared across UI components and callbacks."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal, TypedDict

OverlayId = Literal[
    "states",
    "counties",
    "metros",
    "transit_lines",
    "transit_stops",
    "parks",
    "city_labels",
    "landmark_labels",
]


class OverlayOption(TypedDict):
    label: str
    value: OverlayId


SubscoreCode = Literal["aucs", "EA", "LCA", "MUHAA", "JEA", "MORR", "CTE", "SOU"]


class SubscoreOption(TypedDict):
    label: str
    value: SubscoreCode


class BasemapOption(TypedDict):
    label: str
    value: str


class MapboxLayer(TypedDict, total=False):
    """Subset of mapbox layer attributes used by the UI."""

    sourcetype: str
    source: Mapping[str, object]
    type: str
    color: str
    line: Mapping[str, object]
    below: str
    name: str


class ScoreboardEntry(TypedDict, total=False):
    """Single metric entry rendered on overview scoreboards."""

    label: str
    value: float
    unit: str | None
    description: str | None


class DownloadPayload(TypedDict):
    """Dash download payload compatible with ``dcc.Download``."""

    content: str
    filename: str
    type: str | None
    base64: bool


__all__ = [
    "BasemapOption",
    "MapboxLayer",
    "DownloadPayload",
    "OverlayId",
    "OverlayOption",
    "ScoreboardEntry",
    "SubscoreCode",
    "SubscoreOption",
]
