from __future__ import annotations

import configparser
import json
import os
import sys
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import pytest
from requests import HTTPError

pytest_plugins = [
    "tests.config.conftest",
]

from Urban_Amenities2.cache.manager import CacheConfig, CacheManager
from Urban_Amenities2.ui.config import UISettings
from Urban_Amenities2.ui.data_loader import DataContext

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _load_package_thresholds() -> dict[str, float]:
    config_path = ROOT / ".coveragerc"
    parser = configparser.ConfigParser()
    parser.optionxform = str
    if not config_path.exists():
        return {}
    try:
        parser.read(config_path, encoding="utf-8")
    except OSError:
        return {}
    if not parser.has_section("thresholds"):
        return {}
    thresholds: dict[str, float] = {}
    for key, value in parser.items("thresholds"):
        if key.lower() == "overall":
            continue
        try:
            thresholds[key] = float(value)
        except ValueError:
            continue
    return thresholds


def _collect_line_rate(xml_root: ET.Element, package: str) -> float:
    total = 0
    covered = 0
    candidates = {package}
    if "." in package:
        candidates.add(package.split(".", 1)[1])
    package_names: set[str] = set()
    for pkg in xml_root.findall(".//package"):
        name = pkg.get("name", "")
        for candidate in candidates:
            if name == candidate or name.startswith(f"{candidate}."):
                package_names.add(name)
                break
    if not package_names:
        return 0.0
    processed: set[str] = set()
    queue = list(package_names)
    while queue:
        pkg_name = queue.pop()
        if pkg_name in processed:
            continue
        processed.add(pkg_name)
        for cls in xml_root.findall(f".//package[@name='{pkg_name}']/classes/class"):
            for line in cls.findall("lines/line"):
                total += 1
                hits = line.get("hits", "0")
                try:
                    if int(hits) > 0:
                        covered += 1
                except ValueError:
                    continue
        prefix = f"{pkg_name}."
        for nested in xml_root.findall(".//package"):
            nested_name = nested.get("name", "")
            if nested_name.startswith(prefix) and nested_name not in processed:
                queue.append(nested_name)
    if total == 0:
        return 0.0
    return (covered / total) * 100.0


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
            {
                "mode": "WALK",
                "duration": 120,
                "distance": 200,
                "from": {"name": "A"},
                "to": {"name": "B"},
            }
        ],
    }
    responses = {"post": {"data": {"plan": {"itineraries": [itinerary]}}}}
    return StubSession(responses)


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session: pytest.Session, exitstatus: pytest.ExitCode) -> None:
    if os.environ.get("PYTEST_DISABLE_COVERAGE_CHECKS"):
        return
    xml_path = ROOT / "coverage.xml"
    if not xml_path.exists():
        return
    thresholds = _load_package_thresholds()
    if not thresholds:
        return
    try:
        root = ET.parse(xml_path).getroot()
    except ET.ParseError:
        return

    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    metrics: dict[str, float] = {}
    failures: list[str] = []
    for package, required in thresholds.items():
        rate = _collect_line_rate(root, package)
        metrics[package] = rate
        if rate + 1e-6 < required:
            failures.append(f"{package} coverage {rate:.2f}% is below required {required:.2f}%")

    if reporter and metrics:
        reporter.write_sep("-", "module coverage summary")
        for package in sorted(metrics):
            reporter.write_line(
                f"{package}: {metrics[package]:.2f}% (target {thresholds[package]:.2f}%)"
            )

    if failures:
        if reporter:
            reporter.write_sep("-", "coverage threshold failures")
            for message in failures:
                reporter.write_line(message)
        failed_code = pytest.ExitCode.TESTS_FAILED
        if isinstance(exitstatus, pytest.ExitCode):
            if exitstatus.value < failed_code.value:
                session.exitstatus = failed_code
        else:
            session.exitstatus = max(int(exitstatus), failed_code.value)
