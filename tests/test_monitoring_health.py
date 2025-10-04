from __future__ import annotations

import os
import types
from pathlib import Path
from typing import Any

import requests

from Urban_Amenities2.monitoring.health import (
    HealthStatus,
    format_report,
    overall_status,
    run_health_checks,
)


class DummyResponse:
    def __init__(self, status_code: int, payload: dict[str, Any] | None = None) -> None:
        self.status_code = status_code
        self._payload = payload or {}

    def json(self) -> dict[str, Any]:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"status {self.status_code}")


def test_run_health_checks_success(monkeypatch, tmp_path):
    params_path = Path("configs/params_default.yml")
    data_path = tmp_path / "sample.parquet"
    data_path.write_text("dummy")

    psutil_stub = types.SimpleNamespace(
        disk_usage=lambda _: types.SimpleNamespace(free=200 * 1024**3),
        virtual_memory=lambda: types.SimpleNamespace(available=64 * 1024**3),
    )
    monkeypatch.setattr("Urban_Amenities2.monitoring.health.psutil", psutil_stub, raising=False)

    def fake_get(url: str, timeout: int) -> DummyResponse:  # pragma: no cover - patched
        return DummyResponse(200, {"status": "ok"})

    def fake_post(url: str, json: dict[str, Any], timeout: int) -> DummyResponse:
        return DummyResponse(200, {"data": {"__typename": "Query"}})

    monkeypatch.setattr("requests.get", fake_get)
    monkeypatch.setattr("requests.post", fake_post)

    results = run_health_checks(
        osrm_urls={
            "car": "http://osrm.car",
            "bike": "http://osrm.bike",
            "foot": "http://osrm.foot",
        },
        otp_url="http://otp/graphql",
        params_path=params_path,
        data_paths=[(data_path, 7)],
        min_disk_gb=10,
        min_memory_gb=4,
    )

    status_map = {result.name: result.status for result in results}
    assert status_map["osrm:car"] == HealthStatus.OK
    assert status_map["otp"] == HealthStatus.OK
    assert status_map["params"] == HealthStatus.OK
    assert status_map["data:sample.parquet"] == HealthStatus.OK
    assert status_map["disk"] == HealthStatus.OK
    assert status_map["memory"] == HealthStatus.OK

    assert overall_status(results) == HealthStatus.OK
    report = format_report(results)
    assert "✅ osrm:car" in report


def test_run_health_checks_warn_on_stale_data(monkeypatch, tmp_path):
    params_path = Path("configs/params_default.yml")
    stale_path = tmp_path / "stale.parquet"
    stale_path.write_text("old")
    ninety_one_days = 91 * 24 * 3600
    os.utime(
        stale_path,
        (
            stale_path.stat().st_atime - ninety_one_days,
            stale_path.stat().st_mtime - ninety_one_days,
        ),
    )

    psutil_stub = types.SimpleNamespace(
        disk_usage=lambda _: types.SimpleNamespace(free=200 * 1024**3),
        virtual_memory=lambda: types.SimpleNamespace(available=64 * 1024**3),
    )
    monkeypatch.setattr("Urban_Amenities2.monitoring.health.psutil", psutil_stub, raising=False)

    monkeypatch.setattr("requests.get", lambda url, timeout: DummyResponse(200))
    monkeypatch.setattr(
        "requests.post",
        lambda url, json, timeout: DummyResponse(200, {"data": {"__typename": "Query"}}),
    )

    results = run_health_checks(
        osrm_urls={"car": "http://osrm"},
        otp_url="http://otp/graphql",
        params_path=params_path,
        data_paths=[(stale_path, 7)],
        min_disk_gb=10,
        min_memory_gb=4,
    )

    status_map = {result.name: result.status for result in results}
    assert status_map["data:stale.parquet"] == HealthStatus.WARNING


def test_run_health_checks_reports_failures(monkeypatch, tmp_path):
    missing_params = tmp_path / "missing.yml"
    missing_data = tmp_path / "missing.parquet"

    psutil_stub = types.SimpleNamespace(
        disk_usage=lambda _: types.SimpleNamespace(free=1 * 1024**3),
        virtual_memory=lambda: types.SimpleNamespace(available=int(0.5 * 1024**3)),
    )
    monkeypatch.setattr("Urban_Amenities2.monitoring.health.PSUTIL", psutil_stub, raising=False)

    def failing_get(url: str, timeout: int) -> DummyResponse:  # pragma: no cover - patched
        raise requests.ConnectionError("boom")

    def graphql_errors(url: str, json: dict[str, Any], timeout: int) -> DummyResponse:
        return DummyResponse(200, {"errors": ["bad"]})

    monkeypatch.setattr("requests.get", failing_get)
    monkeypatch.setattr("requests.post", graphql_errors)

    results = run_health_checks(
        osrm_urls={"car": "http://osrm", "bike": None},
        otp_url="http://otp/graphql",
        params_path=missing_params,
        data_paths=[(missing_data, 3)],
        min_disk_gb=10,
        min_memory_gb=4,
    )

    status_map = {result.name: result.status for result in results}
    assert status_map["osrm:car"] == HealthStatus.CRITICAL
    assert status_map["osrm:bike"] == HealthStatus.CRITICAL
    assert status_map["otp"] == HealthStatus.WARNING
    assert status_map["params"] == HealthStatus.CRITICAL
    assert status_map["data:missing.parquet"] == HealthStatus.CRITICAL
    assert status_map["disk"] == HealthStatus.CRITICAL
    assert status_map["memory"] == HealthStatus.CRITICAL

    assert overall_status(results) == HealthStatus.CRITICAL

    report = format_report(results)
    assert "OSRM health check failed" in report
    assert "Parameter validation failed" in report
    assert "Required data file missing" in report
    assert "required_gb" in report
    assert "available_gb" in report
