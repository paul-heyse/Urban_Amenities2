from __future__ import annotations

from typing import Any, Protocol

import pandas as pd

from Urban_Amenities2.io.enrichment.wikipedia import ResponseProtocol, SessionProtocol
from Urban_Amenities2.utils.resilience import CircuitBreakerProtocol, RateLimiterProtocol

__all__ = [
    "CircuitBreakerProtocol",
    "RateLimiterProtocol",
    "ResponseProtocol",
    "SessionProtocol",
    "WikipediaClientProtocol",
    "WikidataClientProtocol",
]


class WikipediaClientProtocol(Protocol):
    """Protocol describing the subset of :class:`WikipediaClient` used in tests."""

    def fetch(self, title: str, *, months: int = ...) -> pd.DataFrame:
        ...


class WikidataClientProtocol(Protocol):
    """Protocol describing the Wikidata client interface used in tests."""

    def query(self, sparql: str) -> dict[str, Any]:
        ...
