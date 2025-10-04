"""Runtime helpers for narrowing common union types.

These utilities complement :mod:`typing` casts by enforcing runtime
validation.  They allow us to satisfy static type checkers such as mypy while
also failing fast when a caller provides an unexpected object at runtime.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from pandas import DataFrame, Series

__all__ = ["cast_to_dataframe", "ensure_dataframe"]


def cast_to_dataframe(obj: DataFrame | Series[Any]) -> DataFrame:
    """Return *obj* if it is already a :class:`~pandas.DataFrame`.

    Parameters
    ----------
    obj:
        Either a :class:`~pandas.DataFrame` or :class:`~pandas.Series`.  The
        helper enforces that a DataFrame is provided and raises :class:`TypeError`
        otherwise.

    Raises
    ------
    TypeError
        If ``obj`` is a :class:`~pandas.Series`.  The message includes the
        object's class name to aid debugging.
    """

    if isinstance(obj, pd.DataFrame):
        return obj
    raise TypeError(
        "Expected pandas DataFrame, received"
        f" {obj.__class__.__name__ if hasattr(obj, '__class__') else type(obj)}"
    )


def ensure_dataframe(obj: DataFrame | Series[Any]) -> DataFrame:
    """Coerce *obj* into a DataFrame.

    Unlike :func:`cast_to_dataframe`, this helper promotes Series objects to a
    single-column DataFrame by using :meth:`Series.to_frame`.  The resulting
    column name is preserved when available or falls back to ``"value"`` to keep
    downstream code predictable.
    """

    if isinstance(obj, pd.DataFrame):
        return obj
    if isinstance(obj, pd.Series):
        column_name = obj.name if obj.name is not None else "value"
        return obj.to_frame(name=column_name)
    raise TypeError(
        "ensure_dataframe expected pandas DataFrame or Series, received"
        f" {obj.__class__.__name__ if hasattr(obj, '__class__') else type(obj)}"
    )

