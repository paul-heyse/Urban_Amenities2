from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import TypeVar

import pytest

T = TypeVar("T")


@dataclass(slots=True)
class DummyRateLimiter:
    """Rate limiter that records calls without sleeping."""

    calls: int = 0

    def acquire(self) -> float:
        self.calls += 1
        return 0.0


@dataclass(slots=True)
class DummyCircuitBreaker:
    """Circuit breaker that optionally raises a stored error."""

    error: Exception | None = None
    calls: int = 0

    def call(self, func: Callable[[], T]) -> T:
        self.calls += 1
        if self.error is not None:
            raise self.error
        return func()


@pytest.fixture
def dummy_rate_limiter() -> Iterator[DummyRateLimiter]:
    yield DummyRateLimiter()


@pytest.fixture
def dummy_breaker() -> Iterator[DummyCircuitBreaker]:
    yield DummyCircuitBreaker()
