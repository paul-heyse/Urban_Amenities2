"""Performance monitoring utilities."""

from __future__ import annotations

import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from functools import wraps
from statistics import mean
from typing import ParamSpec, TypeVar

import structlog

logger = structlog.get_logger()

P = ParamSpec("P")
T = TypeVar("T")


@contextmanager
def timer(operation: str) -> Iterator[None]:
    """
    Context manager to time operations.

    Args:
        operation: Description of the operation being timed
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        logger.info("operation_timed", operation=operation, elapsed_ms=elapsed * 1000)


def profile_function(func: Callable[P, T]) -> Callable[P, T]:
    """
    Decorator to profile function execution time.

    Args:
        func: Function to profile

    Returns:
        Wrapped function with profiling
    """

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start

        logger.info(
            "function_profiled",
            function=func.__name__,
            elapsed_ms=elapsed * 1000,
            args_count=len(args),
            kwargs_count=len(kwargs),
        )

        return result

    return wrapper


class PerformanceMonitor:
    """Monitor and track UI performance metrics."""

    def __init__(self) -> None:
        """Initialize performance monitor."""
        self.metrics: dict[str, list[float]] = {}

    def record(self, metric_name: str, value: float) -> None:
        """
        Record a performance metric.

        Args:
            metric_name: Name of the metric (e.g., 'query_time_ms', 'render_time_ms')
            value: Metric value
        """
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []

        self.metrics[metric_name].append(value)

        # Keep only last 1000 values to avoid unbounded growth
        if len(self.metrics[metric_name]) > 1000:
            self.metrics[metric_name] = self.metrics[metric_name][-1000:]

    def get_stats(self, metric_name: str) -> dict[str, float] | None:
        """
        Get statistics for a metric.

        Args:
            metric_name: Name of the metric

        Returns:
            Dictionary with min, max, mean, p50, p95, p99
        """
        if metric_name not in self.metrics or not self.metrics[metric_name]:
            return None

        values = list(self.metrics[metric_name])
        values_sorted = sorted(values)
        count = len(values_sorted)

        def percentile(pct: float) -> float:
            if not values_sorted:
                return 0.0
            index = min(count - 1, int(round((pct / 100) * (count - 1))))
            return values_sorted[index]

        return {
            "min": float(values_sorted[0]),
            "max": float(values_sorted[-1]),
            "mean": float(mean(values_sorted)),
            "p50": percentile(50),
            "p95": percentile(95),
            "p99": percentile(99),
            "count": count,
        }

    def get_all_stats(self) -> dict[str, dict[str, float]]:
        """Get statistics for all tracked metrics."""
        return {name: stats for name in self.metrics if (stats := self.get_stats(name)) is not None}


# Global performance monitor instance
monitor = PerformanceMonitor()
