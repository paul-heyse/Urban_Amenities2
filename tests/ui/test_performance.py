from __future__ import annotations

import pytest

from Urban_Amenities2.ui import performance


class _CaptureLogger:
    """Simple stand-in for the structlog logger used in performance helpers."""

    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, object]]] = []

    def info(self, event: str, **payload: object) -> None:
        self.events.append((event, dict(payload)))


class FakeTime:
    def __init__(self) -> None:
        self._calls = 0

    def perf_counter(self) -> float:
        value = self._calls * 0.05
        self._calls += 1
        return value


def test_timer_logs_elapsed_time(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_time = FakeTime()
    monkeypatch.setattr(performance, "time", fake_time)
    logger = _CaptureLogger()
    monkeypatch.setattr(performance, "logger", logger)

    with performance.timer("load-data"):
        pass

    assert ("operation_timed", {"operation": "load-data", "elapsed_ms": 50.0}) in [
        (event, {"operation": payload.get("operation"), "elapsed_ms": payload.get("elapsed_ms")})
        for event, payload in logger.events
    ]


def test_profile_function_logs(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_time = FakeTime()
    monkeypatch.setattr(performance, "time", fake_time)
    logger = _CaptureLogger()
    monkeypatch.setattr(performance, "logger", logger)

    @performance.profile_function
    def add(a: int, b: int) -> int:
        return a + b

    assert add(1, 2) == 3

    assert any(event == "function_profiled" for event, _payload in logger.events)


def test_performance_monitor_statistics() -> None:
    monitor = performance.PerformanceMonitor()
    for value in [10.0, 20.0, 30.0]:
        monitor.record("load", value)

    stats = monitor.get_stats("load")
    assert stats is not None
    assert stats["min"] == pytest.approx(10.0)
    assert stats["max"] == pytest.approx(30.0)
    assert stats["mean"] == pytest.approx(20.0)
    assert stats["count"] == 3

    assert monitor.get_stats("missing") is None
    all_stats = monitor.get_all_stats()
    assert "load" in all_stats
