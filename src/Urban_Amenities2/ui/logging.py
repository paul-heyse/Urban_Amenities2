"""Logging helpers for the UI application."""

from __future__ import annotations

import logging
from logging import Logger

from ..logging_utils import get_logger


def configure_logging(level: str = "INFO") -> Logger:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO))
    return get_logger("ui")


__all__ = ["configure_logging"]
