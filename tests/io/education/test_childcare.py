from __future__ import annotations

import pandas as pd
import pytest

from Urban_Amenities2.io.education import childcare


@pytest.fixture(autouse=True)
def patch_points_to_hex(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_points_to_hex(frame: pd.DataFrame, **_: object) -> pd.DataFrame:
        frame = frame.copy()
        frame["hex_id"] = [f"hex-{idx}" for idx in range(len(frame))]
        return frame

    monkeypatch.setattr(childcare, "points_to_hex", _fake_points_to_hex)


def test_normalize_registry_requires_columns() -> None:
    frame = pd.DataFrame({"provider_id": [1], "name": ["Center"], "Latitude": [40.0], "Longitude": [-105.0], "capacity": [30]})
    normalised = childcare.normalize_registry(frame, "CO")
    assert normalised.loc[0, "state"] == "CO"
    with pytest.raises(ValueError):
        childcare.normalize_registry(frame.drop(columns=["capacity"]), "CO")


def test_combine_registries_assigns_hex() -> None:
    registries = {"CO": pd.DataFrame({"facility_id": ["1"], "name": ["Center"], "lat": [40.0], "lon": [-105.0], "capacity": [30]})}
    combined = childcare.combine_registries(registries)
    assert combined.loc[0, "hex_id"].startswith("hex-")
