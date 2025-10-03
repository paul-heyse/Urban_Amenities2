from __future__ import annotations

from collections.abc import Mapping

import pytest

from Urban_Amenities2.ui import layers


class StubContext:
    def __init__(self, overlays: Mapping[str, Mapping[str, object]]) -> None:
        self._overlays = overlays

    def get_overlay(self, key: str) -> Mapping[str, object]:
        return self._overlays.get(key, {"type": "FeatureCollection", "features": []})


def _feature_collection(feature: Mapping[str, object]) -> Mapping[str, object]:
    return {"type": "FeatureCollection", "features": [dict(feature)]}


def test_basemap_helpers() -> None:
    options = layers.basemap_options()
    values = {option["value"] for option in options}
    assert "mapbox://styles/mapbox/streets-v11" in values

    resolved = layers.resolve_basemap_style("carto-positron")
    assert resolved == "carto-positron"
    assert layers.resolve_basemap_style("unknown") == "mapbox://styles/mapbox/streets-v11"

    attribution = layers.basemap_attribution("carto-positron")
    assert "Carto" in attribution


def test_build_overlay_payload_with_selected_layers() -> None:
    overlays_map = {
        "states": _feature_collection(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]]],
                },
                "properties": {"label": "CO"},
            }
        ),
        "transit_lines": _feature_collection(
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[-105.0, 39.7], [-104.9, 39.8]],
                },
                "properties": {"label": "Line"},
            }
        ),
        "parks": _feature_collection(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0.0, 0.0], [0.5, 0.0], [0.5, 0.5], [0.0, 0.5], [0.0, 0.0]]],
                },
                "properties": {"label": "Park"},
            }
        ),
    }
    context = StubContext(overlays_map)

    payload = layers.build_overlay_payload(
        ["states", "transit_lines", "parks", "city_labels"],
        context,
        opacity=0.4,
    )

    assert payload.layers
    assert any(layer["type"] == "fill" for layer in payload.layers)
    assert any(layer["type"] == "line" for layer in payload.layers)
    assert payload.traces  # city_labels adds a Scattermapbox trace


@pytest.mark.parametrize(
    "selection",
    [[], ["unknown"]],
)
def test_build_overlay_payload_without_matches(selection: list[str]) -> None:
    context = StubContext({})
    payload = layers.build_overlay_payload(selection, context)
    assert payload.layers == []
    assert payload.traces == []
