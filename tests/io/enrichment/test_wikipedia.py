from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import pandas as pd
import pytest
import requests

from Urban_Amenities2.io.enrichment import wikipedia
from Urban_Amenities2.utils.resilience import CircuitBreakerOpenError
from tests.io.protocols import ResponseProtocol, SessionProtocol


class StubResponse(ResponseProtocol):
    def __init__(self, payload: dict[str, Any], *, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code
        self.url = "https://example/wikipedia"

    def json(self) -> dict[str, Any]:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError("error")


class RecordingSession(SessionProtocol):
    def __init__(self, responses: list[StubResponse]) -> None:
        self._responses = responses
        self.calls = 0
        self.last_url: str | None = None

    def _pop(self) -> StubResponse:
        if not self._responses:
            raise AssertionError("no responses left")
        return self._responses.pop(0)

    def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> StubResponse:
        self.calls += 1
        self.last_url = url
        return self._pop()

    def post(
        self,
        url: str,
        *,
        data: dict[str, Any] | None = None,
        json: Any | None = None,
        timeout: float | None = None,
    ) -> StubResponse:
        self.calls += 1
        self.last_url = url
        return self._pop()

    def request(
        self,
        method: str,
        url: str,
        *,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> StubResponse:
        self.calls += 1
        self.last_url = url
        return self._pop()


def _patch_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(wikipedia, "retry_with_backoff", lambda func, **_: func())


def test_fetch_uses_cache_on_request_failure(
    tmp_path: Path,
    dummy_rate_limiter,
    dummy_breaker,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
        session=session,
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

    client.session = RecordingSession([])

    class FailingSession(SessionProtocol):
        def get(
            self,
            url: str,
            *,
            params: dict[str, Any] | None = None,
            timeout: float | None = None,
        ) -> StubResponse:
            raise requests.RequestException("boom")

        def post(
            self,
            url: str,
            *,
            data: dict[str, Any] | None = None,
            json: Any | None = None,
            timeout: float | None = None,
        ) -> StubResponse:
            raise requests.RequestException("boom")

        def request(
            self,
            method: str,
            url: str,
            *,
            timeout: float | None = None,
            **kwargs: Any,
        ) -> StubResponse:
            raise requests.RequestException("boom")

    client.session = FailingSession()
    cached = client.fetch("Example Article")
    assert cached.equals(frame)
    assert dummy_breaker.calls == 2


def test_fetch_returns_empty_for_no_items(
    tmp_path: Path,
    dummy_rate_limiter,
    dummy_breaker,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = RecordingSession([StubResponse({"items": []})])
    _patch_retry(monkeypatch)
    client = wikipedia.WikipediaClient(
        cache_dir=tmp_path / "cache",
        session=session,
        rate_limiter=dummy_rate_limiter,
        circuit_breaker=dummy_breaker,
    )
    frame = client.fetch("Missing")
    assert frame.empty


def test_fetch_raises_when_circuit_open_without_cache(
    tmp_path: Path,
    dummy_rate_limiter,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_retry(monkeypatch)
    breaker = wikipedia.CircuitBreaker()
    breaker._state = "open"  # type: ignore[attr-defined]
    breaker._opened_at = breaker.clock()  # type: ignore[attr-defined]
    client = wikipedia.WikipediaClient(
        cache_dir=tmp_path / "cache",
        session=RecordingSession([]),
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


def test_fetch_handles_redirect_payload(
    tmp_path: Path,
    dummy_rate_limiter,
    dummy_breaker,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {"items": [{"timestamp": "2024010100", "views": 0, "type": "redirect"}]}
    session = RecordingSession([StubResponse(payload)])
    _patch_retry(monkeypatch)
    client = wikipedia.WikipediaClient(
        cache_dir=tmp_path / "cache",
        session=session,
        rate_limiter=dummy_rate_limiter,
        circuit_breaker=dummy_breaker,
    )
    frame = client.fetch("Redirect Article")
    assert list(frame["pageviews"]) == [0]


def test_fetch_invokes_retry_wrapper(
    tmp_path: Path,
    dummy_rate_limiter,
    dummy_breaker,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {"items": [{"timestamp": "2024010100", "views": 1}]}
    session = RecordingSession([StubResponse(payload)])
    calls: list[dict[str, Any]] = []

    def _record_retry(func: Callable[[], pd.DataFrame], **kwargs: Any) -> pd.DataFrame:
        calls.append(kwargs)
        return func()

    monkeypatch.setattr(wikipedia, "retry_with_backoff", _record_retry)
    client = wikipedia.WikipediaClient(
        cache_dir=tmp_path / "cache",
        session=session,
        rate_limiter=dummy_rate_limiter,
        circuit_breaker=dummy_breaker,
    )
    frame = client.fetch("Example")
    assert not frame.empty
    assert calls and calls[0]["attempts"] == 3


def test_enrich_with_pageviews_batches_titles(monkeypatch: pytest.MonkeyPatch) -> None:
    called: list[str] = []

    class StubClient:
        def fetch(self, title: str) -> pd.DataFrame:
            called.append(title)
            return pd.DataFrame({"timestamp": [datetime(2024, 1, 1)], "pageviews": [5]})

    titles = {"a": "Title A", "b": "Title B", "c": "Title C"}
    wikipedia.enrich_with_pageviews(titles, client=StubClient())
    assert called == ["Title A", "Title B", "Title C"]
