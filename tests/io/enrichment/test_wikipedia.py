from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import pytest
import requests

from Urban_Amenities2.io.enrichment import wikipedia
from Urban_Amenities2.utils.resilience import CircuitBreakerOpenError


class StubResponse:
    def __init__(self, payload: dict[str, Any], *, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code
        self.url = "https://example/wikipedia"

    def json(self) -> dict[str, Any]:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError("error")


class RecordingSession:
    def __init__(self, responses: list[StubResponse]) -> None:
        self._responses = responses
        self.calls = 0
        self.last_url: str | None = None

    def get(self, url: str, timeout: int) -> StubResponse:
        self.calls += 1
        self.last_url = url
        if not self._responses:
            raise AssertionError("no responses left")
        return self._responses.pop(0)


def _patch_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(wikipedia, "retry_with_backoff", lambda func, **_: func())


def test_fetch_uses_cache_on_request_failure(tmp_path: Path, dummy_rate_limiter, dummy_breaker, monkeypatch: pytest.MonkeyPatch) -> None:  # type: ignore[assignment]
    payload = {
        "items": [
            {"timestamp": "2024010100", "views": 10},
            {"timestamp": "2024020100", "views": 20},
        ]
    }
    session = RecordingSession([StubResponse(payload)])
    _patch_retry(monkeypatch)

    class FixedDatetime(datetime):
        @classmethod
        def utcnow(cls) -> datetime:
            return cls(2024, 3, 15)

        @classmethod
        def now(cls, tz=None):  # type: ignore[override]
            base = cls(2024, 3, 15)
            if tz is not None:
                return base.replace(tzinfo=tz)
            return base

    monkeypatch.setattr(wikipedia, "datetime", FixedDatetime)
    client = wikipedia.WikipediaClient(
        cache_dir=tmp_path / "cache",
        session=session,  # type: ignore[arg-type]
        rate_limiter=dummy_rate_limiter,
        circuit_breaker=dummy_breaker,
    )
    frame = client.fetch("Example Article")
    assert list(frame["pageviews"]) == [10, 20]
    assert session.calls == 1
    assert dummy_rate_limiter.calls == 1
    assert dummy_breaker.calls == 1
    assert session.last_url is not None
    assert "20230306" in session.last_url
    assert "20240229" in session.last_url

    client.session = RecordingSession([])  # type: ignore[assignment]

    def _fail(*args: Any, **kwargs: Any) -> StubResponse:
        raise requests.RequestException("boom")

    client.session.get = _fail  # type: ignore[assignment]
    cached = client.fetch("Example Article")
    assert cached.equals(frame)
    assert dummy_breaker.calls == 2


def test_fetch_returns_empty_for_no_items(tmp_path: Path, dummy_rate_limiter, dummy_breaker, monkeypatch: pytest.MonkeyPatch) -> None:  # type: ignore[assignment]
    session = RecordingSession([StubResponse({"items": []})])
    _patch_retry(monkeypatch)
    client = wikipedia.WikipediaClient(
        cache_dir=tmp_path / "cache",
        session=session,  # type: ignore[arg-type]
        rate_limiter=dummy_rate_limiter,
        circuit_breaker=dummy_breaker,
    )
    frame = client.fetch("Missing")
    assert frame.empty


def test_fetch_raises_when_circuit_open_without_cache(tmp_path: Path, dummy_rate_limiter, monkeypatch: pytest.MonkeyPatch) -> None:  # type: ignore[assignment]
    _patch_retry(monkeypatch)
    breaker = wikipedia.CircuitBreaker()
    breaker._state = "open"  # type: ignore[attr-defined]
    breaker._opened_at = breaker.clock()  # type: ignore[attr-defined]
    client = wikipedia.WikipediaClient(
        cache_dir=tmp_path / "cache",
        session=RecordingSession([]),  # type: ignore[arg-type]
        rate_limiter=dummy_rate_limiter,
        circuit_breaker=breaker,
    )
    with pytest.raises(CircuitBreakerOpenError):
        client.fetch("Example")


def test_compute_statistics() -> None:
    frames = {
        "a": pd.DataFrame({"pageviews": [10, 30, 50]}),
        "b": pd.DataFrame({"pageviews": [5, 5, 5]}),
        "c": pd.DataFrame(columns=["pageviews"]),
    }
    summary = wikipedia.compute_statistics(frames)
    assert set(summary["title"]) == {"a", "b", "c"}
    assert pytest.approx(summary.set_index("title").loc["a", "iqr"]) == 20.0
    assert summary.set_index("title").loc["c", "median_views"] == 0.0


def test_enrich_with_pageviews(monkeypatch: pytest.MonkeyPatch) -> None:
    class StubClient:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def fetch(self, title: str) -> pd.DataFrame:
            self.calls.append(title)
            days = pd.date_range(datetime(2024, 1, 1), periods=2, freq="D")
            return pd.DataFrame({"timestamp": days, "pageviews": [10, 20]})

    client = StubClient()
    titles = {"p1": "Article One", "p2": "Article Two"}
    summary = wikipedia.enrich_with_pageviews(titles, client=client)
    assert set(summary["poi_id"]) == {"p1", "p2"}
    assert all(summary["median_views"] == 15)
    assert client.calls == ["Article One", "Article Two"]
