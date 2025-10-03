from __future__ import annotations

import pytest

from Urban_Amenities2.ui import performance


class FakeTime:
    def __init__(self) -> None:
        self._calls = 0

    def perf_counter(self) -> float:
        value = self._calls * 0.05
        self._calls += 1
        return value


def test_timer_logs_elapsed_time(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    fake_time = FakeTime()
    monkeypatch.setattr(performance, "time", fake_time)

    with caplog.at_level("INFO"), performance.timer("load-data"):
        pass

    assert any("operation_timed" in message for message in caplog.messages)


def test_profile_function_logs(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    fake_time = FakeTime()
    monkeypatch.setattr(performance, "time", fake_time)

    @performance.profile_function
    def add(a: int, b: int) -> int:
        return a + b

    with caplog.at_level("INFO"):
        assert add(1, 2) == 3

    assert any("function_profiled" in message for message in caplog.messages)


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
