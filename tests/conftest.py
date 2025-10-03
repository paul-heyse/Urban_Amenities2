from __future__ import annotations

import json
import sys
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import pytest
from requests import HTTPError

from Urban_Amenities2.cache.manager import CacheConfig, CacheManager
from Urban_Amenities2.ui.config import UISettings
from Urban_Amenities2.ui.data_loader import DataContext

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture(scope="session")
def sample_hex_ids() -> list[str]:
    """Provide a deterministic list of H3 hex IDs for UI fixtures."""

    h3 = pytest.importorskip("h3")
    return [
        h3.latlng_to_cell(39.7392, -104.9903, 9),
        h3.latlng_to_cell(39.8283, -98.5795, 9),
        h3.latlng_to_cell(34.0522, -118.2437, 9),
    ]


@pytest.fixture
def cache_manager(tmp_path: Path) -> Iterator[CacheManager]:
    """Create an isolated cache manager backed by diskcache."""

    config = CacheConfig(cache_dir=tmp_path / "cache", compression=True)
    manager = CacheManager(config)
    try:
        yield manager
    finally:
        manager.clear()
        manager.cache.close()


@pytest.fixture
def ui_dataset_path(tmp_path: Path, sample_hex_ids: list[str]) -> Path:
    """Materialise a minimal UI dataset with scores, metadata, and overlays."""

    data_dir = tmp_path / "ui-data"
    data_dir.mkdir()

    scores = pd.DataFrame(
        {
            "hex_id": sample_hex_ids,
            "aucs": [75.0, 55.0, 65.0],
            "EA": [70.0, 50.0, 60.0],
            "LCA": [68.0, 52.0, 63.0],
            "MUHAA": [66.0, 48.0, 62.0],
            "JEA": [72.0, 53.0, 64.0],
            "MORR": [71.0, 54.0, 61.0],
            "CTE": [69.0, 51.0, 62.0],
            "SOU": [67.0, 49.0, 60.0],
            "state": ["CO", "NE", "CA"],
            "metro": ["Denver", "Lincoln", "Los Angeles"],
            "county": ["Denver", "Lancaster", "Los Angeles"],
        }
    )

    scores_path = data_dir / "20240101_scores.parquet"
    scores.to_parquet(scores_path)

    metadata = scores[["hex_id", "state", "metro", "county"]].copy()
    metadata_path = data_dir / "metadata.parquet"
    metadata.to_parquet(metadata_path)

    # Ensure the score file is treated as the latest dataset
    scores_path.touch()

    overlays_dir = data_dir / "overlays"
    overlays_dir.mkdir()
    (overlays_dir / "transit_lines.geojson").write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [
                                [-104.99, 39.74],
                                [-105.0, 39.75],
                            ],
                        },
                        "properties": {"label": "Test Line"},
                    }
                ],
            }
        )
    )

    (overlays_dir / "parks.geojson").write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [-104.99, 39.74],
                                    [-104.98, 39.74],
                                    [-104.98, 39.75],
                                    [-104.99, 39.75],
                                    [-104.99, 39.74],
                                ]
                            ],
                        },
                        "properties": {"label": "Test Park"},
                    }
                ],
            }
        )
    )

    return data_dir


@pytest.fixture
def ui_settings(ui_dataset_path: Path) -> UISettings:
    """Return UI settings pointing at the generated dataset."""

    return UISettings(
        host="127.0.0.1",
        port=8060,
        debug=False,
        secret_key="test",
        mapbox_token=None,
        cors_origins=["https://example.com"],
        enable_cors=True,
        data_path=ui_dataset_path,
        log_level="DEBUG",
        title="Test Amenities Explorer",
        reload_interval_seconds=15,
        hex_resolutions=[7, 8, 9],
        summary_percentiles=[5, 50, 95],
    )


@pytest.fixture
def data_context(ui_settings: UISettings) -> DataContext:
    """Instantiate a DataContext backed by fixture data."""

    context = DataContext.from_settings(ui_settings)
    context.rebuild_overlays(force=True)
    return context


@pytest.fixture
def timestamp() -> datetime:
    """Utility fixture providing a frozen timestamp for tests."""

    return datetime(2024, 1, 1, 12, 0, 0)


class StubResponse:
    """Minimal response stub compatible with ``requests``."""

    def __init__(self, payload: object, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise HTTPError(f"Stub response returned status {self.status_code}")

    def json(self) -> object:
        return self._payload


class StubSession:
    """Simple HTTP session stub returning canned responses."""

    def __init__(self, responses: dict):
        self.responses = responses
        self.calls: list[str] = []
        self.requests: list[dict[str, object]] = []

    def _lookup(self, method: str, url: str) -> object:
        parsed = urlparse(url)
        path = parsed.path
        candidates: list[object] = [
            (method.upper(), url),
            (method.upper(), path),
            (method.upper(), path.rsplit("/", 1)[-1]),
            method.lower(),
            path,
        ]
        for candidate in candidates:
            if candidate in self.responses:
                return self.responses[candidate]
        for key in self.responses:
            if isinstance(key, str) and key in url:
                return self.responses[key]
        if method.upper() == "GET":
            if "route" in url and "route" in self.responses:
                return self.responses["route"]
            if "table" in url and "table" in self.responses:
                return self.responses["table"]
        if method.upper() == "POST" and "post" in self.responses:
            return self.responses["post"]
        return {}

    def _make_response(self, payload: object) -> StubResponse:
        if isinstance(payload, StubResponse):
            return payload
        status = 200
        body = payload
        if isinstance(payload, tuple) and len(payload) == 2 and isinstance(payload[1], int):
            body, status = payload
        return StubResponse(body, status)

    def get(self, url: str, params=None, timeout: int | None = None):
        self.calls.append(url)
        record = {"method": "GET", "url": url, "params": params or {}, "timeout": timeout}
        self.requests.append(record)
        payload = self._lookup("GET", url)
        return self._make_response(payload)

    def post(self, url: str, json=None, timeout: int | None = None):
        self.calls.append(url)
        record = {"method": "POST", "url": url, "json": json or {}, "timeout": timeout}
        self.requests.append(record)
        payload = self._lookup("POST", url)
        return self._make_response(payload)


@pytest.fixture
def osrm_stub_session() -> StubSession:
    """Provide a stub requests session for OSRM tests."""

    responses = {
        "route": {"code": "Ok", "routes": [{"duration": 100.0, "distance": 200.0, "legs": []}]},
        "table": {"code": "Ok", "durations": [[10.0]], "distances": [[20.0]]},
    }
    return StubSession(responses)


@pytest.fixture
def otp_stub_session() -> StubSession:
    """Provide a stub session for OTP client tests."""

    itinerary = {
        "duration": 600,
        "walkTime": 120,
        "transitTime": 300,
        "waitingTime": 180,
        "transfers": 1,
        "fare": {"fare": {"regular": {"amount": 2.5}}},
        "legs": [
            {"mode": "WALK", "duration": 120, "distance": 200, "from": {"name": "A"}, "to": {"name": "B"}}
        ],
    }
    responses = {"post": {"data": {"plan": {"itineraries": [itinerary]}}}}
    return StubSession(responses)
