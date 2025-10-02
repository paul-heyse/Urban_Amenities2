"""Performance monitoring and optimization utilities."""

from __future__ import annotations

import time
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable

import structlog

logger = structlog.get_logger()


@contextmanager
def timer(operation: str):
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


def profile_function(func: Callable) -> Callable:
    """
    Decorator to profile function execution time.

    Args:
        func: Function to profile

    Returns:
        Wrapped function with profiling
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
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

    def __init__(self):
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

        import numpy as np

        values = np.array(self.metrics[metric_name])

        return {
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "mean": float(np.mean(values)),
            "p50": float(np.percentile(values, 50)),
            "p95": float(np.percentile(values, 95)),
            "p99": float(np.percentile(values, 99)),
            "count": len(values),
        }

    def get_all_stats(self) -> dict[str, dict[str, float]]:
        """Get statistics for all tracked metrics."""
        return {name: self.get_stats(name) for name in self.metrics if self.get_stats(name)}


# Global performance monitor instance
monitor = PerformanceMonitor()

