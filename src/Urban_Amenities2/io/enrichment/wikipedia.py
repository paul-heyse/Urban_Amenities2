"""Wikipedia pageviews enrichment with caching and resiliency."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Protocol, cast

import pandas as pd
import requests
from diskcache import Cache

from ...logging_utils import get_logger
from ...utils.resilience import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitBreakerProtocol,
    RateLimiter,
    RateLimiterProtocol,
    retry_with_backoff,
)

LOGGER = get_logger("aucs.enrichment.wikipedia")

API_URL = (
    "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{project}/all-access/"
    "all-agents/{title}/daily/{start}/{end}"
)


class ResponseProtocol(Protocol):
    """Protocol for HTTP responses consumed by :class:`WikipediaClient`."""

    status_code: int
    url: str | None

    def json(self) -> Any:
        ...

    def raise_for_status(self) -> None:
        ...


class SessionProtocol(Protocol):
    """Protocol capturing the subset of :class:`requests.Session` that we rely on."""

    def get(
        self,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        timeout: float | None = None,
    ) -> ResponseProtocol:
        ...

    def post(
        self,
        url: str,
        *,
        data: Mapping[str, Any] | None = None,
        json: Any | None = None,
        timeout: float | None = None,
    ) -> ResponseProtocol:
        ...

    def request(
        self,
        method: str,
        url: str,
        *,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> ResponseProtocol:
        ...


class WikipediaClient:
    """Client with rate limiting, caching, and graceful fallbacks."""

    def __init__(
        self,
        project: str = "en.wikipedia.org",
        *,
        cache_dir: str | Path = Path("cache/api/wikipedia"),
        cache_ttl_seconds: int = 60 * 60 * 24,
        max_requests_per_sec: int = 100,
        session: SessionProtocol | None = None,
        rate_limiter: RateLimiterProtocol | None = None,
        circuit_breaker: CircuitBreakerProtocol | None = None,
    ) -> None:
        self.project = project
        self.session = cast(SessionProtocol, session or requests.Session())
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache = Cache(directory=str(self.cache_dir), size_limit=10 * 1024**3)
        self.cache_ttl_seconds = cache_ttl_seconds
        self.rate_limiter = cast(
            RateLimiterProtocol,
            rate_limiter or RateLimiter(max_requests_per_sec, per=1.0),
        )
        self.circuit_breaker = cast(
            CircuitBreakerProtocol,
            circuit_breaker
            or CircuitBreaker(
                failure_threshold=5,
                recovery_timeout=60.0,
                expected_exceptions=(requests.RequestException,),
            ),
        )

    def fetch(
        self,
        title: str,
        *,
        months: int = 12,
    ) -> pd.DataFrame:
        """Fetch pageview history for a title, falling back to cached data."""

        key = self._cache_key(title, months)
        cached = self.cache.get(key)
        try:
            data = self._fetch_remote(title, months)
        except CircuitBreakerOpenError:
            LOGGER.error("wikipedia_circuit_open", title=self._safe_title(title))
            if cached is not None:
                return self._to_frame(cached)
            raise
        except requests.RequestException as exc:
            LOGGER.warning("wikipedia_fetch_failed", title=self._safe_title(title), error=str(exc))
            if cached is not None:
                return self._to_frame(cached)
            raise
        if data is None:
            return pd.DataFrame(columns=["timestamp", "pageviews"])
        frame = self._normalise_records(data)
        self.cache.set(key, frame.to_dict("records"), expire=self.cache_ttl_seconds)
        return frame

    # Internal helpers -------------------------------------------------
    def _fetch_remote(self, title: str, months: int) -> list[dict[str, object]] | None:
        def _execute() -> list[dict[str, object]] | None:
            self.rate_limiter.acquire()
            end = datetime.now(UTC).date().replace(day=1) - timedelta(days=1)
            start = end - timedelta(days=30 * months)
            url = API_URL.format(
                project=self.project,
                title=title.replace(" ", "_"),
                start=start.strftime("%Y%m%d"),
                end=end.strftime("%Y%m%d"),
            )
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            payload = response.json()
            items = payload.get("items", [])
            if not isinstance(items, list):
                return []
            return [item for item in items if isinstance(item, dict)]

        def _wrapped() -> list[dict[str, object]] | None:
            return retry_with_backoff(
                _execute,
                attempts=3,
                base_delay=1.0,
                max_delay=4.0,
                jitter=0.25,
                exceptions=(requests.RequestException,),
            )

        return self.circuit_breaker.call(_wrapped)

    def _normalise_records(self, records: list[dict[str, object]]) -> pd.DataFrame:
        if not records:
            return pd.DataFrame(columns=["timestamp", "pageviews"])
        frame = pd.DataFrame.from_records(records)
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], format="%Y%m%d00")
        frame = frame.rename(columns={"views": "pageviews"})
        return frame[["timestamp", "pageviews"]]

    def _cache_key(self, title: str, months: int) -> str:
        digest = hashlib.sha1(title.encode("utf-8")).hexdigest()
        return f"{self.project}:{months}:{digest}"

    @staticmethod
    def _safe_title(title: str) -> str:
        return title[:100]

    @staticmethod
    def _to_frame(records: list[dict[str, object]]) -> pd.DataFrame:
        if not records:
            return pd.DataFrame(columns=["timestamp", "pageviews"])
        frame = pd.DataFrame.from_records(records)
        frame["timestamp"] = pd.to_datetime(frame["timestamp"])
        return frame[["timestamp", "pageviews"]]


def compute_statistics(pageviews: dict[str, pd.DataFrame]) -> pd.DataFrame:
    records = []
    for title, frame in pageviews.items():
        if frame.empty:
            records.append({"title": title, "median_views": 0.0, "iqr": 0.0})
            continue
        median = float(frame["pageviews"].median())
        q1 = float(frame["pageviews"].quantile(0.25))
        q3 = float(frame["pageviews"].quantile(0.75))
        records.append({"title": title, "median_views": median, "iqr": q3 - q1})
    summary = pd.DataFrame.from_records(records)
    if summary.empty:
        return summary
    mean = summary["median_views"].mean()
    std = summary["median_views"].std(ddof=0) or 1.0
    summary["popularity_z"] = (summary["median_views"] - mean) / std
    return summary


def enrich_with_pageviews(
    titles: dict[str, str],
    *,
    client: WikipediaClient | None = None,
) -> pd.DataFrame:
    client = client or WikipediaClient()
    pageview_data: dict[str, pd.DataFrame] = {}
    for poi_id, title in titles.items():
        frame = client.fetch(title)
        pageview_data[poi_id] = frame
    stats = compute_statistics({poi_id: frame for poi_id, frame in pageview_data.items()})
    stats = stats.rename(columns={"title": "poi_id"})
    stats["poi_id"] = stats["poi_id"].astype(str)
    stats["title"] = [titles.get(poi_id, "") for poi_id in stats["poi_id"]]
    return stats


__all__ = [
    "ResponseProtocol",
    "SessionProtocol",
    "WikipediaClient",
    "enrich_with_pageviews",
    "compute_statistics",
    "CircuitBreaker",
]
