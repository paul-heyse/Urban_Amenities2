from __future__ import annotations

import pandas as pd

from Urban_Amenities2.io.education import ipeds


def test_compute_weights_assigns_scores() -> None:
    frame = pd.DataFrame({"carnegie": ["R1 University", "Associate College"]})
    weighted = ipeds.compute_weights(frame)
    assert weighted.loc[0, "q_u"] == 1.0
    assert weighted.loc[1, "q_u"] == 0.4


def test_prepare_universities_merges_and_hexes(monkeypatch) -> None:
    directory = pd.DataFrame(
        {
            "unitid": [1],
            "latitude": [40.0],
            "longitude": [-105.0],
            "name": ["Campus"],
        }
    )
    carnegie = pd.DataFrame({"unitid": [1], "carnegie": ["R1"]})

    def _fake_points_to_hex(frame: pd.DataFrame, **_: object) -> pd.DataFrame:
        return frame.assign(hex_id=["hex-1"])

    monkeypatch.setattr(ipeds, "points_to_hex", _fake_points_to_hex)
    prepared = ipeds.prepare_universities(directory, carnegie)
    assert prepared.loc[0, "hex_id"] == "hex-1"
    assert prepared.loc[0, "q_u"] == 1.0
