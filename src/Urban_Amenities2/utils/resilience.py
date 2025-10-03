"""Utility helpers for rate limiting and resilient API access."""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from threading import Lock
from typing import TypeVar

__all__ = [
    "CircuitBreaker",
    "CircuitBreakerOpenError",
    "RateLimiter",
    "retry_with_backoff",
]


T = TypeVar("T")


class RateLimiter:
    """Simple token bucket rate limiter.

    The limiter blocks the caller when the configured rate would be exceeded.
    A custom ``sleep_func`` can be supplied to ease testing.
    """

    def __init__(
        self,
        rate: float,
        per: float = 1.0,
        *,
        sleep_func: Callable[[float], None] = time.sleep,
    ) -> None:
        if rate <= 0 or per <= 0:
            msg = "rate and period must be positive"
            raise ValueError(msg)
        self.rate = float(rate)
        self.per = float(per)
        self.capacity = self.rate * self.per
        self._tokens = self.capacity
        self._timestamp = time.monotonic()
        self._sleep = sleep_func
        self._lock = Lock()

    def acquire(self) -> float:
        """Block until a token is available and return the wait time."""

        waited = 0.0
        while True:
            with self._lock:
                now = time.monotonic()
                elapsed = now - self._timestamp
                if elapsed > 0:
                    self._tokens = min(
                        self.capacity, self._tokens + elapsed * self.rate
                    )
                self._timestamp = now
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return waited
                missing = 1.0 - self._tokens
                wait_for = missing / self.rate
            self._sleep(wait_for)
            waited += wait_for


class CircuitBreakerOpenError(RuntimeError):
    """Raised when the circuit breaker is open and calls are blocked."""


@dataclass(slots=True)
class CircuitBreaker:
    """Lightweight circuit breaker with half-open recovery state."""

    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    expected_exceptions: tuple[type[BaseException], ...] = (Exception,)
    clock: Callable[[], float] = time.monotonic
    _state: str = "closed"
    _failures: int = 0
    _opened_at: float = 0.0
    _lock: Lock = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.failure_threshold <= 0:
            msg = "failure_threshold must be positive"
            raise ValueError(msg)
        if self.recovery_timeout <= 0:
            msg = "recovery_timeout must be positive"
            raise ValueError(msg)
        object.__setattr__(self, "_lock", Lock())

    # Public API ---------------------------------------------------------
    def call(self, func: Callable[[], T]) -> T:
        """Execute ``func`` respecting the breaker state."""

        self.before_call()
        try:
            result = func()
        except self.expected_exceptions:  # pragma: no cover - exercised via tests
            self.record_failure()
            raise
        else:
            self.record_success()
            return result

    def before_call(self) -> None:
        with self._lock:
            if self._state == "open":
                if self.clock() - self._opened_at >= self.recovery_timeout:
                    self._state = "half-open"
                else:
                    raise CircuitBreakerOpenError("circuit breaker is open")

    def record_success(self) -> None:
        with self._lock:
            self._state = "closed"
            self._failures = 0

    def record_failure(self) -> None:
        with self._lock:
            self._failures += 1
            if self._failures >= self.failure_threshold:
                self._state = "open"
                self._opened_at = self.clock()


def retry_with_backoff[T](
    func: Callable[[], T],
    *,
    attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 4.0,
    jitter: float = 0.1,
    sleep_func: Callable[[float], None] = time.sleep,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
) -> T:
    """Execute ``func`` with exponential backoff and jitter."""

    last_error: BaseException | None = None
    for attempt in range(1, attempts + 1):
        try:
            return func()
        except exceptions as exc:  # pragma: no cover - behaviour verified in tests
            last_error = exc
            if attempt == attempts:
                raise
            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            jitter_amount = delay * jitter
            delay += random.uniform(0, jitter_amount)
            sleep_func(delay)
    assert last_error is not None  # pragma: no cover - defensive
    raise last_error
