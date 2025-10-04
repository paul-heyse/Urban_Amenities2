from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from Urban_Amenities2.io.parks import ridb


@dataclass
class DummyResponse:
    payload: dict[str, Any]
    status_code: int = 200
    url: str = "https://example/ridb"

    def json(self) -> dict[str, Any]:
        return self.payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError("http error")

    @property
    def content(self) -> bytes:
        return b"payload"


class RecordingSession:
    def __init__(self, responses: Iterable[DummyResponse]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def get(self, url: str, *, params: dict[str, Any], headers: dict[str, str] | None, timeout: int) -> DummyResponse:
        self.calls.append({"url": url, "params": params, "headers": headers, "timeout": timeout})
        if not self._responses:
            raise AssertionError("no responses configured")
        return self._responses.pop(0)


class DummyRegistry:
    def __init__(self) -> None:
        self.snapshots: list[tuple[str, str, bytes]] = []
        self.checked: list[tuple[str, bytes]] = []

    def has_changed(self, key: str, data: bytes) -> bool:
        self.checked.append((key, data))
        return True

    def record_snapshot(self, key: str, url: str, data: bytes) -> None:
        self.snapshots.append((key, url, data))


@pytest.fixture(autouse=True)
def patch_points_to_hex(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_points_to_hex(frame: pd.DataFrame, **_: Any) -> pd.DataFrame:
        frame = frame.copy()
        frame["hex_id"] = [f"hex-{idx}" for idx in range(len(frame))]
        return frame

    monkeypatch.setattr(ridb, "points_to_hex", _fake_points_to_hex)


def test_fetch_handles_pagination_and_snapshots() -> None:
    responses = [
        DummyResponse({"RECDATA": [{"RecAreaID": 1, "RecAreaLatitude": 40.0, "RecAreaLongitude": -105.0}], "METADATA": {}}),
        DummyResponse({"RECDATA": []}),
    ]
    session = RecordingSession(responses)
    registry = DummyRegistry()
    ingestor = ridb.RIDBIngestor(ridb.RIDBConfig(page_size=1), registry=registry)
    frame = ingestor.fetch(["CO"], session=session)  # type: ignore[arg-type]
    assert len(frame) == 1
    assert registry.snapshots
    assert session.calls[0]["params"]["state"] == "CO"


def test_index_to_hex_returns_empty_when_no_records() -> None:
    ingestor = ridb.RIDBIngestor()
    frame = pd.DataFrame(columns=["lat", "lon"])
    indexed = ingestor.index_to_hex(frame)
    assert "hex_id" in indexed.columns


def test_ingest_writes_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ingestor = ridb.RIDBIngestor()
    monkeypatch.setattr(ingestor, "fetch", lambda states, session=None: pd.DataFrame({"lat": [40.0], "lon": [-105.0]}))
    output = tmp_path / "ridb.parquet"
    result = ingestor.ingest(["CO"], output_path=output)
    assert output.exists()
    assert not result.empty


def test_fetch_includes_headers_when_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = [
        DummyResponse(
            {
                "RECDATA": [
                    {
                        "RecAreaID": 1,
                        "RecAreaName": "Area",
                        "RecAreaLatitude": 40.0,
                        "RecAreaLongitude": -105.0,
                    }
                ],
                "METADATA": {},
            }
        ),
        DummyResponse({"RECDATA": []}),
    ]
    session = RecordingSession(responses)
    config = ridb.RIDBConfig(api_key="secret", page_size=1)
    ingestor = ridb.RIDBIngestor(config=config, registry=DummyRegistry())
    ingestor.fetch(["CO"], session=session)  # type: ignore[arg-type]
    assert session.calls[0]["headers"] == {"apikey": "secret"}


def test_fetch_handles_incomplete_records() -> None:
    responses = [
        DummyResponse(
            {
                "RECDATA": [
                    {"RecAreaID": 1, "RecAreaName": "Area"}
                ],
                "METADATA": {},
            }
        )
    ]
    session = RecordingSession(responses)
    frame = ridb.RIDBIngestor(registry=DummyRegistry()).fetch(["CO"], session=session)  # type: ignore[arg-type]
    assert frame.loc[0, "lat"] == pytest.approx(0.0)
    assert frame.loc[0, "lon"] == pytest.approx(0.0)


def test_index_to_hex_uses_points_to_hex(monkeypatch: pytest.MonkeyPatch) -> None:
    ingestor = ridb.RIDBIngestor()
    frame = pd.DataFrame({"lat": [40.0], "lon": [-105.0]})
    called: dict[str, Any] = {}

    def _capture_points(frame: pd.DataFrame, **kwargs: Any) -> pd.DataFrame:
        called["kwargs"] = kwargs
        return frame.assign(hex_id=["hex"])

    monkeypatch.setattr(ridb, "points_to_hex", _capture_points)
    indexed = ingestor.index_to_hex(frame)
    assert indexed.loc[0, "hex_id"] == "hex"
    assert called["kwargs"]["hex_column"] == "hex_id"
