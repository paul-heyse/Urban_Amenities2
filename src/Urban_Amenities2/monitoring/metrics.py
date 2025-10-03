from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass, field
from threading import Lock
from types import TracebackType
from typing import Literal

import numpy as np
from structlog.typing import FilteringBoundLogger

from ..logging_utils import get_logger

LOGGER = get_logger("aucs.metrics")


@dataclass(slots=True)
class MetricSummary:
    """Aggregate statistics for a metric bucket."""

    count: int
    total_duration: float
    p50: float
    p95: float
    p99: float
    throughput: float | None = None

    def as_dict(self) -> dict[str, float]:
        data = {
            "count": float(self.count),
            "total_duration": self.total_duration,
            "p50": self.p50,
            "p95": self.p95,
            "p99": self.p99,
        }
        if self.throughput is not None:
            data["throughput_per_second"] = self.throughput
        return data


@dataclass(slots=True)
class _ServiceBucket:
    durations: list[float] = field(default_factory=list)
    success: int = 0
    failure: int = 0

    def record(self, duration: float, *, success: bool) -> None:
        self.durations.append(duration)
        if success:
            self.success += 1
        else:
            self.failure += 1

    def clear(self) -> None:
        self.durations.clear()
        self.success = 0
        self.failure = 0


class MetricsCollector:
    """In-memory metrics collector suitable for unit tests and batch jobs."""

    def __init__(self) -> None:
        self._timings: MutableMapping[str, list[float]] = defaultdict(list)
        self._throughput: MutableMapping[str, list[float]] = defaultdict(list)
        self._service: MutableMapping[str, _ServiceBucket] = {}
        self._lock = Lock()

    def record_timing(self, name: str, duration: float, *, count: int | None = None) -> None:
        if duration < 0:
            raise ValueError("duration must be non-negative")
        with self._lock:
            self._timings[name].append(float(duration))
            if count is not None and duration > 0:
                self._throughput[name].append(count / duration)

    def record_service_call(self, name: str, duration: float, *, success: bool) -> None:
        if duration < 0:
            raise ValueError("duration must be non-negative")
        with self._lock:
            bucket = self._service.get(name)
            if bucket is None:
                bucket = _ServiceBucket()
                self._service[name] = bucket
            bucket.record(float(duration), success=success)

    def record_throughput(self, name: str, rows_processed: int, duration: float) -> None:
        if duration <= 0:
            raise ValueError("duration must be positive")
        with self._lock:
            self._throughput[name].append(rows_processed / duration)

    def timing_summary(self, name: str) -> MetricSummary | None:
        with self._lock:
            durations = list(self._timings.get(name, ()))
            throughput = list(self._throughput.get(name, ()))
        if not durations:
            return None
        array = np.asarray(durations, dtype=float)
        return MetricSummary(
            count=len(durations),
            total_duration=float(array.sum()),
            p50=float(np.percentile(array, 50)),
            p95=float(np.percentile(array, 95)),
            p99=float(np.percentile(array, 99)),
            throughput=float(np.mean(throughput)) if throughput else None,
        )

    def service_summary(self, name: str) -> dict[str, float] | None:
        with self._lock:
            bucket = self._service.get(name)
        if not bucket:
            return None
        durations = np.asarray(bucket.durations, dtype=float)
        summary: dict[str, float] = {
            "success": float(bucket.success),
            "failure": float(bucket.failure),
        }
        if durations.size:
            summary["p50"] = float(np.percentile(durations, 50))
            summary["p95"] = float(np.percentile(durations, 95))
            summary["p99"] = float(np.percentile(durations, 99))
        return summary

    def serialise(self) -> dict[str, Mapping[str, float]]:
        payload: dict[str, Mapping[str, float]] = {}
        with self._lock:
            timing_keys = list(self._timings)
        for name in timing_keys:
            summary = self.timing_summary(name)
            if summary is not None:
                payload[f"timing:{name}"] = summary.as_dict()
        with self._lock:
            service_keys = list(self._service)
        for name in service_keys:
            service = self.service_summary(name)
            if service is not None:
                payload[f"service:{name}"] = service
        return payload

    def clear(self) -> None:
        with self._lock:
            self._timings.clear()
            self._throughput.clear()
            self._service.clear()

    def record(
        self,
        name: str,
        duration: float,
        *,
        count: int | None = None,
        success: bool | None = None,
    ) -> None:
        """Record a timing and optional service outcome in a single call."""

        self.record_timing(name, duration, count=count)
        if success is not None:
            self.record_service_call(name, duration, success=success)


METRICS = MetricsCollector()


class OperationTracker:
    """Context manager that logs and records metrics for an operation."""

    def __init__(
        self,
        name: str,
        *,
        metrics: MetricsCollector | None = None,
        logger: FilteringBoundLogger | None = None,
        items: int | None = None,
        extra: Mapping[str, object] | None = None,
    ) -> None:
        self.name = name
        self.metrics = metrics or METRICS
        self.logger = logger or LOGGER
        self.items = items
        self.extra = dict(extra or {})
        self._start: float | None = None

    def __enter__(self) -> OperationTracker:
        self._start = time.perf_counter()
        if self.logger is not None:
            self.logger.info("operation_start", operation=self.name, items=self.items, **self.extra)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> Literal[False]:
        duration = time.perf_counter() - (self._start or time.perf_counter())
        self.metrics.record_timing(self.name, duration, count=self.items)
        if self.logger is not None:
            event = "operation_error" if exc else "operation_complete"
            context = {"operation": self.name, "duration_seconds": duration}
            if self.items is not None:
                context["items"] = self.items
            context.update(self.extra)
            if exc:
                context["error"] = repr(exc)
            self.logger.info(event, **context)
        return False


def track_operation(
    name: str,
    *,
    metrics: MetricsCollector | None = None,
    logger: FilteringBoundLogger | None = None,
    items: int | None = None,
    extra: Mapping[str, object] | None = None,
) -> OperationTracker:
    """Helper to create an :class:`OperationTracker` context manager."""

    return OperationTracker(name, metrics=metrics, logger=logger, items=items, extra=extra)


__all__ = [
    "MetricSummary",
    "MetricsCollector",
    "METRICS",
    "OperationTracker",
    "track_operation",
]
