"""Wikidata enrichment utilities with resiliency safeguards."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
from SPARQLWrapper import JSON, SPARQLWrapper
from diskcache import Cache

from ...logging_utils import get_logger
from ...utils.resilience import CircuitBreaker, CircuitBreakerOpenError, RateLimiter, retry_with_backoff

LOGGER = get_logger("aucs.enrichment.wikidata")


@dataclass
class WikidataClient:
    endpoint: str = "https://query.wikidata.org/sparql"
    user_agent: str = "UrbanAmenitiesBot/0.1"
    cache_dir: str | Path = Path("cache/api/wikidata")
    cache_ttl_seconds: int = 60 * 60 * 24 * 7
    rate_limit_per_sec: int = 10

    def __post_init__(self) -> None:
        self._client = SPARQLWrapper(self.endpoint, agent=self.user_agent)
        self._client.setReturnFormat(JSON)
        cache_dir = Path(self.cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache = Cache(directory=str(cache_dir), size_limit=10 * 1024**3)
        self._rate_limiter = RateLimiter(self.rate_limit_per_sec, per=1.0)
        self._breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60.0,
            expected_exceptions=(Exception,),
        )

    def query(self, query: str) -> Dict:
        key = self._cache_key(query)
        cached = self._cache.get(key)
        try:
            result = self._execute(query)
        except CircuitBreakerOpenError:
            LOGGER.error("wikidata_circuit_open")
            if cached is not None:
                return cached
            raise
        except Exception as exc:  # pragma: no cover - tested via fallback
            LOGGER.warning("wikidata_query_failed", error=str(exc))
            if cached is not None:
                return cached
            raise
        self._cache.set(key, result, expire=self.cache_ttl_seconds)
        return result

    def _execute(self, query: str) -> Dict:
        def _call() -> Dict:
            self._rate_limiter.acquire()
            self._client.setQuery(query)
            response = self._client.query()
            return response.convert()

        return self._breaker.call(
            lambda: retry_with_backoff(
                _call,
                attempts=3,
                base_delay=1.0,
                max_delay=4.0,
                jitter=0.25,
                exceptions=(Exception,),
            )
        )

    @staticmethod
    def _cache_key(query: str) -> str:
        return hashlib.sha1(query.encode("utf-8")).hexdigest()


def build_query(name: str, lat: float, lon: float, radius_km: float = 0.5) -> str:
    return f"""
    SELECT ?item ?itemLabel ?capacity ?heritage WHERE {{
      ?item rdfs:label "{name}"@en.
      SERVICE wikibase:around {{
        ?item wdt:P625 ?location .
        bd:serviceParam wikibase:center "Point({lon} {lat})"^^geo:wktLiteral .
        bd:serviceParam wikibase:radius "{radius_km}" .
      }}
      OPTIONAL {{ ?item wdt:P1083 ?capacity. }}
      OPTIONAL {{ ?item wdt:P1435 ?heritage. }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}
    LIMIT 1
    """


class WikidataEnricher:
    def __init__(self, client: WikidataClient | None = None) -> None:
        self.client = client or WikidataClient()

    def match(self, name: str, lat: float, lon: float) -> Dict[str, Optional[str]]:
        query = build_query(name, lat, lon)
        response = self.client.query(query)
        bindings = response.get("results", {}).get("bindings", [])
        if not bindings:
            return {"wikidata_qid": None, "capacity": None, "heritage_status": None}
        binding = bindings[0]
        qid = binding.get("item", {}).get("value", "")
        qid_short = qid.split("/")[-1] if qid else None
        capacity = binding.get("capacity", {}).get("value")
        heritage = binding.get("heritage", {}).get("value")
        return {"wikidata_qid": qid_short, "capacity": capacity, "heritage_status": heritage}

    def enrich(self, pois: pd.DataFrame) -> pd.DataFrame:
        records = []
        for _, row in pois.iterrows():
            result = self.match(
                row.get("name", ""),
                float(row.get("lat", 0.0)),
                float(row.get("lon", 0.0)),
            )
            records.append({"poi_id": row.get("poi_id"), **result})
        return pd.DataFrame.from_records(records)


__all__ = ["WikidataClient", "WikidataEnricher", "build_query"]
