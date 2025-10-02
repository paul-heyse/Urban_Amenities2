from __future__ import annotations

import pandas as pd
import requests

from Urban_Amenities2.io.enrichment.wikipedia import WikipediaClient
from Urban_Amenities2.utils.resilience import CircuitBreaker, RateLimiter


class DummyResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload
        self.status_code = 200

    def json(self) -> dict:
        return self._payload

    def raise_for_status(self) -> None:  # pragma: no cover - always OK
        return None


class DummySession:
    def __init__(self, responses: list[object]) -> None:
        self.responses = responses
        self.calls = 0

    def get(self, url: str, timeout: int) -> DummyResponse:
        index = min(self.calls, len(self.responses) - 1)
        response = self.responses[index]
        self.calls += 1
        if isinstance(response, Exception):
            raise response
        return response  # type: ignore[return-value]


def _rate_limiter() -> RateLimiter:
    return RateLimiter(rate=100, per=1.0, sleep_func=lambda _: None)


def _circuit_breaker() -> CircuitBreaker:
    return CircuitBreaker(
        failure_threshold=2,
        recovery_timeout=1.0,
        expected_exceptions=(requests.RequestException,),
    )


def test_wikipedia_client_caches_and_falls_back(tmp_path):
    records = [{"timestamp": "2024010100", "views": 10}]
    session = DummySession([DummyResponse({"items": records}), requests.HTTPError("boom")])
    client = WikipediaClient(
        session=session,
        cache_dir=tmp_path / "wiki",
        rate_limiter=_rate_limiter(),
        circuit_breaker=_circuit_breaker(),
    )

    frame = client.fetch("Denver")
    assert isinstance(frame, pd.DataFrame)
    assert not frame.empty
    assert session.calls == 1

    frame_cached = client.fetch("Denver")
    assert session.calls > 1
    pd.testing.assert_frame_equal(frame, frame_cached)
