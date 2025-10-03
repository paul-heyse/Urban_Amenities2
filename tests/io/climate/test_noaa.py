from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from Urban_Amenities2.io.climate import noaa


@dataclass
class StubResponse:
    payload: Any
    status_code: int = 200
    url: str = "https://example/noaa"

    def json(self) -> Any:
        return self.payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError("http error")

    @property
    def content(self) -> bytes:
        return b"payload"


class StubSession:
    def __init__(self, responses: Iterable[StubResponse]) -> None:
        self._responses = list(responses)
        self.calls: list[tuple[str, dict[str, Any], dict[str, Any] | None]] = []

    def get(
        self, url: str, *, params: dict[str, Any], headers: dict[str, str] | None, timeout: int
    ) -> StubResponse:
        self.calls.append((url, params, headers))
        if not self._responses:
            raise AssertionError("no responses configured")
        return self._responses.pop(0)


class DummyRegistry:
    def __init__(self) -> None:
        self.snapshots: list[tuple[str, str, bytes]] = []
        self.changed: list[tuple[str, bytes]] = []

    def has_changed(self, source: str, data: bytes) -> bool:
        self.changed.append((source, data))
        return True

    def record_snapshot(self, source: str, url: str, data: bytes) -> None:
        self.snapshots.append((source, url, data))


def test_fetch_normalises_columns() -> None:
    records = [
        {
            "station": f"00{i}",
            "month": f"{i:02d}",
            "MLY-TAVG-NORMAL": str(10 + i),
            "MLY-PRCP-PRB": str(10 * i),
            "MLY-WSF2-NORMAL": str(3 + i),
            "latitude": "45.0",
            "longitude": "7.0",
        }
        for i in range(1, 13)
    ]
    response = StubResponse(records)
    session = StubSession([response])
    registry = DummyRegistry()
    ingestor = noaa.NoaaNormalsIngestor(registry=registry)
    frame = ingestor.fetch("CO", session=session)  # type: ignore[arg-type]
    assert session.calls[0][1]["state"] == "CO"
    assert set(frame.columns) >= {"month", "tavg_c", "precip_probability", "wind_mps", "state"}
    assert frame.loc[0, "month"] == 1
    assert frame.loc[11, "month"] == 12
    assert frame.loc[0, "tavg_c"] == pytest.approx(11.0)
    assert frame.loc[0, "precip_probability"] == pytest.approx(0.1)
    assert registry.snapshots


def test_fetch_rejects_unexpected_payload() -> None:
    session = StubSession([StubResponse({"items": []})])
    ingestor = noaa.NoaaNormalsIngestor()
    with pytest.raises(ValueError):
        ingestor.fetch("CO", session=session)  # type: ignore[arg-type]


def test_interpolate_to_hex(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_latlon_to_hex(lat: float, lon: float, resolution: int) -> str:
        return f"hex-{lat:.1f}-{lon:.1f}-{resolution}"

    monkeypatch.setattr(noaa, "latlon_to_hex", _fake_latlon_to_hex)
    ingestor = noaa.NoaaNormalsIngestor()
    frame = pd.DataFrame({"latitude": [40.0, 41.0], "longitude": [-104.0, -105.0], "month": [1, 2]})
    result = ingestor.interpolate_to_hex(frame, resolution=8)
    assert set(result["hex_id"]) == {"hex-40.0--104.0-8", "hex-41.0--105.0-8"}


def test_compute_comfort_index() -> None:
    frame = pd.DataFrame(
        {
            "hex_id": ["a", "a", "b"],
            "month": [1, 1, 1],
            "tavg_c": [15.0, 16.0, None],
            "precip_probability": [0.2, 0.1, None],
            "wind_mps": [3.0, 5.0, None],
        }
    )
    ingestor = noaa.NoaaNormalsIngestor()
    comfort = ingestor.compute_comfort_index(frame)
    assert len(comfort) == 2
    assert (
        comfort.set_index("hex_id").loc["a", "sigma_out"]
        > comfort.set_index("hex_id").loc["b", "sigma_out"]
    )


def test_ingest_writes_parquet(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    response = StubResponse(
        [
            {
                "station": "001",
                "month": "01",
                "MLY-TAVG-NORMAL": "10",
                "latitude": "40",
                "longitude": "-105",
            }
        ]
    )
    session = StubSession([response])

    def _fake_latlon_to_hex(lat: float, lon: float, resolution: int) -> str:
        return "hex"

    monkeypatch.setattr(noaa, "latlon_to_hex", _fake_latlon_to_hex)
    ingestor = noaa.NoaaNormalsIngestor(registry=DummyRegistry())
    output_path = tmp_path / "comfort.parquet"
    comfort = ingestor.ingest(["CO"], session=session, output_path=output_path)  # type: ignore[arg-type]
    assert output_path.exists()
    assert not comfort.empty


def test_fetch_states_combines_results(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = [
        StubResponse(
            [
                {
                    "station": "001",
                    "month": "01",
                    "MLY-TAVG-NORMAL": "10",
                    "latitude": "40",
                    "longitude": "-105",
                }
            ]
        ),
        StubResponse(
            [
                {
                    "station": "002",
                    "month": "02",
                    "MLY-TAVG-NORMAL": "5",
                    "latitude": "41",
                    "longitude": "-104",
                }
            ]
        ),
    ]
    session = StubSession(responses)
    registry = DummyRegistry()
    ingestor = noaa.NoaaNormalsIngestor(registry=registry)
    frame = ingestor.fetch_states(["CO", "UT"], session=session)  # type: ignore[arg-type]
    assert len(frame) == 2
    assert registry.snapshots and len(registry.snapshots) == 2


def test_interpolate_to_hex_empty_returns_expected_columns() -> None:
    ingestor = noaa.NoaaNormalsIngestor()
    result = ingestor.interpolate_to_hex(pd.DataFrame())
    assert list(result.columns) == ["hex_id", "month", "tavg_c", "precip_probability", "wind_mps"]


def test_compute_comfort_index_handles_empty_frame() -> None:
    ingestor = noaa.NoaaNormalsIngestor()
    result = ingestor.compute_comfort_index(pd.DataFrame())
    assert list(result.columns) == ["hex_id", "month", "sigma_out"]
