from __future__ import annotations

from Urban_Amenities2.ui.callbacks import (
    _extract_viewport_bounds,
    _normalise_filters,
    _normalise_overlays,
    _resolution_for_zoom,
)


def test_normalise_filters_and_overlays() -> None:
    assert _normalise_filters(None) == []
    assert _normalise_filters("CO") == ["CO"]
    assert _normalise_filters(["CO", "", "UT"]) == ["CO", "UT"]

    overlays = _normalise_overlays(["states", "unknown", "parks"])
    assert overlays == ["states", "parks"]


def test_resolution_for_zoom_thresholds() -> None:
    assert _resolution_for_zoom(None) == 8
    assert _resolution_for_zoom(4.5) == 6
    assert _resolution_for_zoom(7.2) == 7
    assert _resolution_for_zoom(10.5) == 8
    assert _resolution_for_zoom(12.0) == 9


def test_extract_viewport_bounds_from_coordinates() -> None:
    relayout = {
        "mapbox._derived": {
            "coordinates": [
                [[-105.0, 39.7], [-104.9, 39.7], [-104.9, 39.8], [-105.0, 39.8]],
            ]
        }
    }
    bounds = _extract_viewport_bounds(relayout, None)
    assert bounds == (-105.0, 39.7, -104.9, 39.8)


def test_extract_viewport_bounds_from_center_zoom() -> None:
    relayout = {
        "mapbox.center.lon": -105.0,
        "mapbox.center.lat": 39.7,
        "mapbox.zoom": 8.0,
    }
    fallback = (-106.0, 38.5, -104.0, 40.5)
    bounds = _extract_viewport_bounds(relayout, fallback)
    assert bounds is not None
    assert bounds[0] < relayout["mapbox.center.lon"]
    assert bounds[2] > relayout["mapbox.center.lon"]


def test_extract_viewport_bounds_invalid_returns_fallback() -> None:
    fallback = (-1.0, -1.0, 1.0, 1.0)
    assert _extract_viewport_bounds({}, fallback) == fallback
    assert _extract_viewport_bounds(None, fallback) == fallback
