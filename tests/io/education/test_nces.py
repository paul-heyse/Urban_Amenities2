from __future__ import annotations

import pandas as pd
import pytest

from Urban_Amenities2.io.education import nces


@pytest.fixture(autouse=True)
def patch_points_to_hex(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_points_to_hex(frame: pd.DataFrame, **_: object) -> pd.DataFrame:
        frame = frame.copy()
        frame["hex_id"] = [f"hex-{idx}" for idx in range(len(frame))]
        return frame

    monkeypatch.setattr(nces, "points_to_hex", _fake_points_to_hex)


def _sample_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "NCESSCH": ["1"],
            "SCH_NAME": ["Example"],
            "LAT": [40.0],
            "LON": [-105.0],
            "LEVEL": ["High"],
            "ENR_TOTAL": [100],
            "TOTFTE": [10],
        }
    )


def test_prepare_schools_combines_public_and_private() -> None:
    public = _sample_frame()
    private = _sample_frame().assign(NCESSCH="2")
    combined = nces.prepare_schools(public, private)
    assert set(combined["school_id"]) == {"1", "2"}
    assert all(combined["student_teacher_ratio"] == 10.0)


def test_prepare_schools_raises_on_missing_columns() -> None:
    public = _sample_frame().drop(columns=["LEVEL"])
    with pytest.raises(ValueError):
        nces.prepare_schools(public, _sample_frame())
