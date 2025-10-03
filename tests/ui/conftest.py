from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from types import SimpleNamespace

import pandas as pd
import pytest

from Urban_Amenities2.ui import data_loader, export, hex_selection, hexes


@dataclass
class FakeShape:
    coordinates: list[tuple[float, float]]

    @property
    def is_empty(self) -> bool:
        return not self.coordinates

    def simplify(self, _tolerance: float, preserve_topology: bool = True) -> FakeShape:
        return self


class FakeH3:
    """Minimal stand-in for the ``h3`` module used in UI utilities."""

    def __init__(self) -> None:
        self.boundary_calls: list[str] = []
        self.centroid_calls: list[str] = []
        self.parent_requests: list[tuple[str, int]] = []

    @staticmethod
    def _base_coords(hex_id: str) -> tuple[float, float]:
        seed = sum(ord(ch) for ch in hex_id)
        lon = -105.0 + (seed % 10) * 0.01
        lat = 39.0 + ((seed // 10) % 10) * 0.01
        return lon, lat

    def cell_to_boundary(self, hex_id: str) -> list[list[float]]:
        self.boundary_calls.append(hex_id)
        lon, lat = self._base_coords(hex_id)
        return [
            [lat, lon],
            [lat + 0.01, lon],
            [lat + 0.01, lon + 0.01],
            [lat, lon + 0.01],
        ]

    def cell_to_latlng(self, hex_id: str) -> tuple[float, float]:
        self.centroid_calls.append(hex_id)
        lon, lat = self._base_coords(hex_id)
        return lat + 0.005, lon + 0.005

    @staticmethod
    def get_resolution(_hex_id: str) -> int:
        return 9

    def cell_to_parent(self, hex_id: str, resolution: int) -> str:
        self.parent_requests.append((hex_id, resolution))
        return f"{hex_id[:8]}_r{resolution}"

    def grid_disk(self, hex_id: str, k: int) -> list[str]:
        return [hex_id, *[f"{hex_id}-n{i}" for i in range(1, k + 1)]]

    def k_ring(self, hex_id: str, k: int = 1) -> list[str]:
        return self.grid_disk(hex_id, k)


@pytest.fixture
def fake_h3(monkeypatch: pytest.MonkeyPatch) -> FakeH3:
    """Provide a shared fake H3 module for UI tests."""

    stub = FakeH3()

    monkeypatch.setattr(hexes, "_load_h3", lambda: stub)
    monkeypatch.setattr(hex_selection, "_import_h3", lambda: stub)
    monkeypatch.setattr(data_loader, "_import_h3", lambda: stub)
    monkeypatch.setattr(export, "_h3", lambda: stub)

    yield stub

    hexes._hex_boundary_geojson.cache_clear()
    hexes._hex_boundary_wkt.cache_clear()
    hexes._hex_centroid.cache_clear()


@pytest.fixture
def fake_shapely(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch shapely helpers used by the data loader to avoid real dependency."""

    def _parse_wkt(payload: str) -> FakeShape:
        inner = payload.strip().removeprefix("POLYGON((").removesuffix("))")
        coordinates: list[tuple[float, float]] = []
        for part in inner.split(","):
            part = part.strip()
            if not part:
                continue
            lon_str, lat_str = part.split()
            coordinates.append((float(lon_str), float(lat_str)))
        return FakeShape(coordinates)

    def _mapping(shape: FakeShape) -> dict[str, object]:
        return {
            "type": "Polygon",
            "coordinates": [[list(coord) for coord in shape.coordinates]],
        }

    def _unary_union(shapes: Iterable[FakeShape]) -> FakeShape:
        shapes = list(shapes)
        if not shapes:
            return FakeShape([])
        return FakeShape(list(shapes[0].coordinates))

    monkeypatch.setattr(
        data_loader,
        "_import_shapely_modules",
        lambda: (SimpleNamespace(loads=_parse_wkt), _mapping, _unary_union),
    )


@pytest.fixture
def sample_scores() -> pd.DataFrame:
    """Create a deterministic scores DataFrame for selection tests."""

    data = {
        "hex_id": ["abc123", "def456", "ghi789"],
        "aucs": [75.0, 80.0, 90.0],
        "EA": [70.0, 65.0, 85.0],
        "state": ["CO", "CO", "UT"],
        "metro": ["Denver", "Boulder", "Salt Lake City"],
        "county": ["Denver", "Boulder", "Salt Lake"],
        "top_amenities": [
            [{"name": "Library", "category": "Education", "score": 0.95}],
            [],
            [{"name": "Cafe", "category": "Food", "score": 0.8}],
        ],
        "top_modes": [
            {"transit": 0.4, "walk": 0.2},
            {"drive": 0.6},
            {"bike": 0.3},
        ],
    }
    return pd.DataFrame(data)
