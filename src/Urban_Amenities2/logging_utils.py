"""Structlog configuration helpers."""
from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from typing import Any, Callable, Iterator

import structlog
from structlog.typing import FilteringBoundLogger


def configure_logging(level: str = "INFO") -> None:
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level.upper(), logging.INFO)),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "aucs") -> FilteringBoundLogger:
    return structlog.get_logger(name)


def bind_context(logger: FilteringBoundLogger, **context: Any) -> FilteringBoundLogger:
    return logger.bind(**context)


@contextmanager
def log_duration(logger: FilteringBoundLogger, event: str, **context: Any) -> Iterator[None]:
    start = time.perf_counter()
    yield
    duration = time.perf_counter() - start
    logger.info(event, duration_seconds=duration, **context)


def timing_decorator(logger: FilteringBoundLogger, event: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.perf_counter() - start
                logger.info(event, duration_seconds=duration)

        return wrapper

    return decorator
