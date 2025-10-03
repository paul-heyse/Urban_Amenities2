from __future__ import annotations

import pandas as pd
import pytest

from Urban_Amenities2.io.airports import faa


@pytest.fixture(autouse=True)
def patch_points_to_hex(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_points_to_hex(frame: pd.DataFrame, **_: object) -> pd.DataFrame:
        frame = frame.copy()
        frame["hex_id"] = [f"hex-{idx}" for idx in range(len(frame))]
        return frame

    monkeypatch.setattr(faa, "points_to_hex", _fake_points_to_hex)


def test_filter_states_filters_case_insensitive() -> None:
    frame = pd.DataFrame({"STATE": ["CO", "WY"], "LAT": [40.0, 41.0], "LON": [-105.0, -106.0]})
    filtered = faa.filter_states(frame, ["co"])
    assert set(filtered["STATE"]) == {"CO"}


def test_compute_weights_handles_zero_total() -> None:
    frame = pd.DataFrame({"ENPLANEMENTS": [0, 0]})
    weighted = faa.compute_weights(frame)
    assert all(weighted["weight"] == 0.0)


def test_ingest_airports_writes_output(tmp_path, monkeypatch) -> None:
    frame = pd.DataFrame({"STATE": ["CO"], "ENPLANEMENTS": [100], "LAT": [40.0], "LON": [-105.0]})
    monkeypatch.setattr(faa, "load_enplanements", lambda path: frame)
    output = tmp_path / "airports.parquet"
    result = faa.ingest_airports("airports.csv", ["CO"], output_path=output)
    assert output.exists()
    assert result.loc[0, "weight"] == 1.0
