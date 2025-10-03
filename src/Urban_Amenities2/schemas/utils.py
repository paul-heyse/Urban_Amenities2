"""Utility decorators for schema validation in pipelines."""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import TypeVar

import pandera as pa

T = TypeVar("T")


def validate_with_schema(
    schema: pa.DataFrameSchema,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator that validates the first pandas DataFrame argument against a schema."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not args:
                raise ValueError("validate_with_schema expects the DataFrame as the first argument")
            schema.validate(args[0])
            result = func(*args, **kwargs)
            return result

        return wrapper

    return decorator
