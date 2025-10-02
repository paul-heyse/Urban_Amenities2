from __future__ import annotations

import types

import pytest

from Urban_Amenities2.utils.resilience import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    RateLimiter,
    retry_with_backoff,
)


def test_rate_limiter_waits_when_exhausted(monkeypatch):
    waits: list[float] = []
    limiter = RateLimiter(rate=2, per=1.0, sleep_func=waits.append)
    assert limiter.acquire() == 0
    assert limiter.acquire() == 0
    waited = limiter.acquire()
    assert pytest.approx(waited) == pytest.approx(sum(waits))
    assert waits and waits[0] > 0


def test_circuit_breaker_transitions():
    clock_state = types.SimpleNamespace(value=0.0)

    def fake_clock() -> float:
        return clock_state.value

    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=5.0, clock=fake_clock)
    breaker.before_call()
    breaker.record_failure()
    breaker.record_failure()
    with pytest.raises(CircuitBreakerOpenError):
        breaker.before_call()
    clock_state.value = 10.0
    breaker.before_call()  # transitions to half-open
    breaker.record_success()
    breaker.before_call()  # closed again


def test_retry_with_backoff_retries_and_succeeds():
    attempts: list[int] = []

    def flaky() -> str:
        attempts.append(len(attempts))
        if len(attempts) < 3:
            raise ValueError("boom")
        return "ok"

    waits: list[float] = []
    result = retry_with_backoff(
        flaky,
        attempts=3,
        base_delay=1.0,
        max_delay=5.0,
        jitter=0.0,
        sleep_func=waits.append,
        exceptions=(ValueError,),
    )
    assert result == "ok"
    assert waits == [1.0, 2.0]


def test_retry_with_backoff_raises_after_exhaustion():
    def always_fail() -> str:
        raise RuntimeError("nope")

    with pytest.raises(RuntimeError):
        retry_with_backoff(
            always_fail,
            attempts=2,
            base_delay=0.1,
            jitter=0.0,
            sleep_func=lambda _: None,
            exceptions=(RuntimeError,),
        )
