from __future__ import annotations

import pandas as pd
import pytest

from Urban_Amenities2.utils.types import cast_to_dataframe, ensure_dataframe


def test_cast_to_dataframe_accepts_dataframe() -> None:
    frame = pd.DataFrame({"value": [1, 2, 3]})
    result = cast_to_dataframe(frame)
    assert result is frame


def test_cast_to_dataframe_rejects_series() -> None:
    series = pd.Series([1, 2, 3], name="value")
    with pytest.raises(TypeError):
        cast_to_dataframe(series)


def test_ensure_dataframe_promotes_series() -> None:
    series = pd.Series([1, 2], name="example")
    frame = ensure_dataframe(series)
    expected = series.to_frame()
    pd.testing.assert_frame_equal(frame, expected)


def test_ensure_dataframe_adds_default_column_name() -> None:
    series = pd.Series([1, 2])
    frame = ensure_dataframe(series)
    assert list(frame.columns) == ["value"]
