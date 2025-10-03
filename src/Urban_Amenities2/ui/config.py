"""Environment-driven configuration for the Urban Amenities UI."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from ..logging_utils import get_logger

LOGGER = get_logger("ui.config")


@dataclass(slots=True)
class UISettings:
    """Configuration state for the Dash application."""

    host: str = field(default_factory=lambda: os.getenv("UI_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("UI_PORT", "8050")))
    debug: bool = field(default_factory=lambda: os.getenv("UI_DEBUG", "false").lower() == "true")
    secret_key: str = field(default_factory=lambda: os.getenv("UI_SECRET_KEY", "change-me"))
    mapbox_token: str | None = field(default_factory=lambda: os.getenv("MAPBOX_TOKEN"))
    cors_origins: list[str] = field(default_factory=lambda: _split_env("UI_CORS_ORIGINS", "*"))
    enable_cors: bool = field(
        default_factory=lambda: os.getenv("UI_ENABLE_CORS", "true").lower() == "true"
    )
    data_path: Path = field(default_factory=lambda: Path(os.getenv("UI_DATA_PATH", "data/outputs")))
    log_level: str = field(default_factory=lambda: os.getenv("UI_LOG_LEVEL", "INFO"))
    title: str = field(default_factory=lambda: os.getenv("UI_TITLE", "Urban Amenities Explorer"))
    reload_interval_seconds: int = field(
        default_factory=lambda: int(os.getenv("UI_RELOAD_INTERVAL", "30"))
    )
    hex_resolutions: list[int] = field(
        default_factory=lambda: _split_int_env("UI_HEX_RESOLUTIONS", "6,7,8,9")
    )
    summary_percentiles: list[int] = field(
        default_factory=lambda: _split_int_env("UI_SUMMARY_PERCENTILES", "5,25,50,75,95")
    )

    @classmethod
    def from_environment(cls) -> UISettings:
        settings = cls()
        LOGGER.info(
            "ui_settings_loaded",
            host=settings.host,
            port=settings.port,
            data_path=str(settings.data_path),
            debug=settings.debug,
        )
        return settings


def _split_env(name: str, default: str) -> list[str]:
    value = os.getenv(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


def _split_int_env(name: str, default: str) -> list[int]:
    return [int(item) for item in _split_env(name, default)]


__all__ = ["UISettings"]
