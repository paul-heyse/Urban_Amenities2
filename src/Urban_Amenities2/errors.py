"""Error classification helpers for AUCS pipelines."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ErrorCategory(str, Enum):
    DATA = "data"
    CONFIG = "config"
    COMPUTATION = "computation"


@dataclass(slots=True)
class ClassifiedError(Exception):
    category: ErrorCategory
    message: str
    context: dict[str, Any] | None = None

    def __str__(self) -> str:  # pragma: no cover - trivial
        base = f"[{self.category.value}] {self.message}"
        if self.context:
            return f"{base} | context={self.context}"
        return base


class DataQualityError(ClassifiedError):
    def __init__(self, message: str, **context: Any) -> None:
        super().__init__(ErrorCategory.DATA, message, context or None)


class ConfigurationError(ClassifiedError):
    def __init__(self, message: str, **context: Any) -> None:
        super().__init__(ErrorCategory.CONFIG, message, context or None)


class ComputationError(ClassifiedError):
    def __init__(self, message: str, **context: Any) -> None:
        super().__init__(ErrorCategory.COMPUTATION, message, context or None)
