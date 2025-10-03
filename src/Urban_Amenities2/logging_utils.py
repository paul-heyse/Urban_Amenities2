"""Structured logging utilities with sanitisation and context management."""

from __future__ import annotations

import contextvars
import hashlib
import logging
import logging.handlers
from collections.abc import Iterable, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import structlog
from structlog.typing import FilteringBoundLogger

__all__ = [
    "bind_context",
    "configure_logging",
    "get_logger",
    "log_duration",
    "request_context",
    "timing_decorator",
]


_REQUEST_ID: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)


def configure_logging(level: str = "INFO", *, log_file: str | Path | None = None) -> None:
    """Configure structlog with JSON output and optional file logging."""

    numeric_level = getattr(logging, level.upper(), logging.INFO)
    handlers: list[logging.Handler] = []

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter("%(message)s"))
    handlers.append(stream_handler)

    if log_file:
        path = Path(log_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            path, maxBytes=100 * 1024 * 1024, backupCount=10
        )
        file_handler.setFormatter(logging.Formatter("%(message)s"))
        handlers.append(file_handler)

    logging.basicConfig(level=numeric_level, handlers=handlers, force=True)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            _sanitise_event,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "aucs") -> FilteringBoundLogger:
    return structlog.get_logger(name)


def bind_context(logger: FilteringBoundLogger, **context: Any) -> FilteringBoundLogger:
    return logger.bind(**context)


@contextmanager
def request_context(request_id: str) -> Iterable[None]:
    token = _REQUEST_ID.set(request_id)
    try:
        yield
    finally:
        _REQUEST_ID.reset(token)


@contextmanager
def log_duration(logger: FilteringBoundLogger, event: str, **context: Any) -> Iterable[None]:
    import time

    start = time.perf_counter()
    try:
        yield
    finally:
        duration = time.perf_counter() - start
        logger.info(event, duration_seconds=duration, **context)


def timing_decorator(logger: FilteringBoundLogger, event: str):
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time

            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.perf_counter() - start
                logger.info(event, duration_seconds=duration)

        return wrapper

    return decorator


def _sanitise_event(
    _: FilteringBoundLogger,
    __: str,
    event_dict: Mapping[str, Any],
) -> Mapping[str, Any]:
    mutable = dict(event_dict)
    request_id = _REQUEST_ID.get()
    if request_id and "request_id" not in mutable:
        mutable["request_id"] = request_id
    for key, value in list(mutable.items()):
        if _is_secret_key(key):
            mutable[key] = "***"
        elif _is_coordinate_field(key):
            mutable[key] = _round_value(value)
        elif key == "coords":
            mutable[key] = _round_coords(value)
        elif key in {"user_id", "user"} and isinstance(value, str):
            mutable[key] = hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
    return mutable


def _is_secret_key(key: str) -> bool:
    lowered = key.lower()
    return "api_key" in lowered or lowered.endswith("_token")


def _is_coordinate_field(key: str) -> bool:
    lowered = key.lower()
    return lowered in {"lat", "latitude", "lon", "longitude"}


def _round_value(value: Any) -> Any:
    if isinstance(value, (int, float)):
        return round(float(value), 3)
    return value


def _round_coords(value: Any) -> Any:
    if isinstance(value, (list, tuple)):
        rounded = []
        for item in value:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                rounded.append((_round_value(item[0]), _round_value(item[1])))
            else:
                rounded.append(_round_value(item))
        return rounded
    return value
