"""Utilities for map layers and overlay styling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, TYPE_CHECKING

import plotly.graph_objects as go

if TYPE_CHECKING:  # pragma: no cover - typing only
    from .data_loader import DataContext


@dataclass(frozen=True)
class OverlayPayload:
    """Container for mapbox layers and additional Plotly traces."""

    layers: List[dict]
    traces: List[go.BaseTraceType]


_BASEMAP_STYLES: Dict[str, Dict[str, str]] = {
    "mapbox://styles/mapbox/streets-v11": {
        "label": "Streets",
        "attribution": "© Mapbox © OpenStreetMap",
    },
    "mapbox://styles/mapbox/outdoors-v11": {
        "label": "Outdoors",
        "attribution": "© Mapbox © OpenStreetMap",
    },
    "mapbox://styles/mapbox/satellite-streets-v12": {
        "label": "Satellite",
        "attribution": "© Mapbox © Maxar",
    },
    "mapbox://styles/mapbox/dark-v10": {
        "label": "Dark",
        "attribution": "© Mapbox © OpenStreetMap",
    },
    "open-street-map": {
        "label": "OpenStreetMap",
        "attribution": "© OpenStreetMap contributors",
    },
    "carto-positron": {
        "label": "Carto Positron",
        "attribution": "© CartoDB",
    },
}


_CITY_FEATURES: List[dict] = [
    {
        "type": "Feature",
        "properties": {"label": "Denver"},
        "geometry": {"type": "Point", "coordinates": [-104.9903, 39.7392]},
    },
    {
        "type": "Feature",
        "properties": {"label": "Salt Lake City"},
        "geometry": {"type": "Point", "coordinates": [-111.8910, 40.7608]},
    },
    {
        "type": "Feature",
        "properties": {"label": "Boise"},
        "geometry": {"type": "Point", "coordinates": [-116.2023, 43.6150]},
    },
    {
        "type": "Feature",
        "properties": {"label": "Colorado Springs"},
        "geometry": {"type": "Point", "coordinates": [-104.8214, 38.8339]},
    },
]


_LANDMARK_FEATURES: List[dict] = [
    {
        "type": "Feature",
        "properties": {"label": "DEN Airport"},
        "geometry": {"type": "Point", "coordinates": [-104.6737, 39.8561]},
    },
    {
        "type": "Feature",
        "properties": {"label": "SLC Airport"},
        "geometry": {"type": "Point", "coordinates": [-111.9807, 40.7899]},
    },
    {
        "type": "Feature",
        "properties": {"label": "Boise State University"},
        "geometry": {"type": "Point", "coordinates": [-116.2029, 43.6030]},
    },
    {
        "type": "Feature",
        "properties": {"label": "Arches National Park"},
        "geometry": {"type": "Point", "coordinates": [-109.5925, 38.7331]},
    },
]


_OVERLAY_COLOR = {
    "states": "#2563eb",
    "counties": "#6b7280",
    "metros": "#f97316",
    "transit_lines": "#10b981",
    "parks": "#22c55e",
}


def basemap_options() -> List[dict]:
    """Return dropdown options for map styles."""

    return [
        {"label": meta["label"], "value": value}
        for value, meta in _BASEMAP_STYLES.items()
    ]


def resolve_basemap_style(style: str | None) -> str:
    """Return a recognised map style value."""

    if style and style in _BASEMAP_STYLES:
        return style
    return "mapbox://styles/mapbox/streets-v11"


def basemap_attribution(style: str | None) -> str:
    """Retrieve attribution text for a given map style."""

    meta = _BASEMAP_STYLES.get(resolve_basemap_style(style))
    return meta.get("attribution", "© Mapbox © OpenStreetMap") if meta else ""


def build_overlay_payload(
    selected: Iterable[str],
    context: "DataContext",
    *,
    opacity: float = 0.35,
) -> OverlayPayload:
    """Build mapbox layers and Plotly traces for the selected overlays."""

    selected_set = {value for value in (selected or []) if value}
    layers: List[dict] = []
    traces: List[go.BaseTraceType] = []
    clamped_opacity = max(0.0, min(opacity, 1.0))

    def _rgba(color: str, alpha: float) -> str:
        color = color.lstrip("#")
        r, g, b = (int(color[i : i + 2], 16) for i in (0, 2, 4))
        return f"rgba({r},{g},{b},{alpha:.3f})"

    def _boundary_layers(key: str, name: str, alpha_multiplier: float = 0.35) -> None:
        if key not in selected_set:
            return
        geojson = context.get_overlay(key)
        if not geojson.get("features"):
            return
        color = _OVERLAY_COLOR.get(key, "#111827")
        layers.extend(
            [
                {
                    "sourcetype": "geojson",
                    "source": geojson,
                    "type": "fill",
                    "color": _rgba(color, clamped_opacity * alpha_multiplier),
                    "below": "traces",
                    "name": f"{name} (fill)",
                },
                {
                    "sourcetype": "geojson",
                    "source": geojson,
                    "type": "line",
                    "color": color,
                    "line": {"width": 2},
                    "name": f"{name} (outline)",
                },
            ]
        )

    _boundary_layers("states", "States", alpha_multiplier=0.15)
    _boundary_layers("counties", "Counties", alpha_multiplier=0.1)
    _boundary_layers("metros", "Metros", alpha_multiplier=0.25)

    if "transit_lines" in selected_set:
        lines = context.get_overlay("transit_lines")
        if lines.get("features"):
            layers.append(
                {
                    "sourcetype": "geojson",
                    "source": lines,
                    "type": "line",
                    "color": _OVERLAY_COLOR["transit_lines"],
                    "line": {"width": 3},
                    "name": "Transit lines",
                }
            )

    if "parks" in selected_set:
        parks = context.get_overlay("parks")
        if parks.get("features"):
            layers.append(
                {
                    "sourcetype": "geojson",
                    "source": parks,
                    "type": "fill",
                    "color": _rgba(_OVERLAY_COLOR["parks"], clamped_opacity * 0.5),
                    "below": "traces",
                    "name": "Parks & trails",
                }
            )

    def _point_trace(features: Sequence[dict], name: str, marker: dict, text_only: bool = False) -> None:
        if not features:
            return
        lon: List[float] = []
        lat: List[float] = []
        labels: List[str] = []
        for feature in features:
            geometry = feature.get("geometry") or {}
            if geometry.get("type") != "Point":
                continue
            coords = geometry.get("coordinates") or []
            if len(coords) < 2:
                continue
            lon.append(coords[0])
            lat.append(coords[1])
            label = feature.get("properties", {}).get("label")
            labels.append(label or name)
        if not lon:
            return
        mode = "text" if text_only else "markers+text"
        trace = go.Scattermapbox(
            lon=lon,
            lat=lat,
            mode=mode,
            name=name,
            text=labels,
            textposition="top center",
            textfont={"size": 12 + int(clamped_opacity * 6)},
            marker=marker,
            hoverinfo="text",
        )
        traces.append(trace)

    if "transit_stops" in selected_set:
        stops = context.get_overlay("transit_stops")
        _point_trace(
            stops.get("features", []),
            "Transit stops",
            {"size": 9, "color": "#0ea5e9", "opacity": 0.85},
        )

    if "city_labels" in selected_set:
        _point_trace(
            _CITY_FEATURES,
            "City labels",
            {"size": 1, "color": "rgba(0,0,0,0)", "opacity": 0.0},
            text_only=True,
        )

    if "landmark_labels" in selected_set:
        _point_trace(
            _LANDMARK_FEATURES,
            "Landmarks",
            {"size": 1, "color": "rgba(0,0,0,0)", "opacity": 0.0},
            text_only=True,
        )

    return OverlayPayload(layers=layers, traces=traces)


__all__ = [
    "OverlayPayload",
    "basemap_attribution",
    "basemap_options",
    "build_overlay_payload",
    "resolve_basemap_style",
]
