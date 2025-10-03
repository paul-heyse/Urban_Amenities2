from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from Urban_Amenities2.io.enrichment import wikidata


def test_build_query_contains_coordinates() -> None:
    query = wikidata.build_query("Central Park", 40.0, -73.9, radius_km=1.2)
    assert "Central Park" in query
    assert "-73.9" in query
    assert "1.2" in query


def test_wikidata_enricher_match_returns_fields() -> None:
    class StubClient:
        def query(self, _: str) -> dict[str, object]:
            return {
                "results": {
                    "bindings": [
                        {
                            "item": {"value": "https://www.wikidata.org/entity/Q123"},
                            "capacity": {"value": "1000"},
                            "heritage": {"value": "Q234"},
                        }
                    ]
                }
            }

    enricher = wikidata.WikidataEnricher(client=StubClient())
    result = enricher.match("Place", 40.0, -73.9)
    assert result == {"wikidata_qid": "Q123", "capacity": "1000", "heritage_status": "Q234"}


def test_wikidata_enricher_handles_missing_results() -> None:
    class EmptyClient:
        def query(self, _: str) -> dict[str, object]:
            return {"results": {"bindings": []}}

    enricher = wikidata.WikidataEnricher(client=EmptyClient())
    result = enricher.match("Unknown", 0.0, 0.0)
    assert result == {"wikidata_qid": None, "capacity": None, "heritage_status": None}


def test_wikidata_enricher_enriches_dataframe() -> None:
    class RecordingClient:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def query(self, _: str) -> dict[str, object]:
            self.calls.append("called")
            return {"results": {"bindings": []}}

    pois = pd.DataFrame(
        {"poi_id": ["a", "b"], "name": ["One", "Two"], "lat": [1.0, 2.0], "lon": [3.0, 4.0]}
    )
    client = RecordingClient()
    enricher = wikidata.WikidataEnricher(client=client)
    result = enricher.enrich(pois)
    assert len(result) == 2
    assert all(result["wikidata_qid"].isna())
    assert client.calls == ["called", "called"]


class DummyCache(dict[str, Any]):
    def set(self, key: str, value: Any, expire: int | None = None) -> None:
        self[key] = value


def test_wikidata_client_returns_cache_on_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    client = wikidata.WikidataClient(cache_dir=tmp_path)
    client._cache = DummyCache()  # type: ignore[assignment]
    cached_key = client._cache_key("SELECT 1")
    client._cache.set(cached_key, {"results": {"bindings": []}})
    monkeypatch.setattr(client, "_execute", lambda query: (_ for _ in ()).throw(Exception("boom")))
    result = client.query("SELECT 1")
    assert result["results"] == {"bindings": []}


def test_wikidata_client_retries_on_transient_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = wikidata.WikidataClient(cache_dir=tmp_path)
    client._cache = DummyCache()  # type: ignore[assignment]

    class StubResponse:
        def convert(self) -> dict[str, object]:
            return {"results": {"bindings": []}}

    class StubClient:
        def __init__(self) -> None:
            self.calls = 0

        def setQuery(self, query: str) -> None:  # noqa: N802 - external API signature
            self.calls += 1

        def query(self) -> StubResponse:  # noqa: N802 - external API signature
            return StubResponse()

    calls = {"retry": 0}

    def _fake_retry(func: Any, **_: Any) -> Any:
        calls["retry"] += 1
        return func()

    breaker = type("Breaker", (), {"call": lambda self, func: func()})()
    rate_limiter = type("Limiter", (), {"acquire": lambda self: 0.0})()
    client._client = StubClient()  # type: ignore[assignment]
    client._breaker = breaker  # type: ignore[assignment]
    client._rate_limiter = rate_limiter  # type: ignore[assignment]
    monkeypatch.setattr(wikidata, "retry_with_backoff", _fake_retry)

    result = client.query("SELECT ?item WHERE {}")
    assert result == {"results": {"bindings": []}}
    assert calls["retry"] == 1
