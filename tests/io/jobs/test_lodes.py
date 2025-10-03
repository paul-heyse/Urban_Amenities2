from __future__ import annotations

import pandas as pd
import pytest

from Urban_Amenities2.io.jobs import lodes


@pytest.fixture(autouse=True)
def patch_points_to_hex(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_points_to_hex(frame: pd.DataFrame, **_: object) -> pd.DataFrame:
        frame = frame.copy()
        frame["hex_id"] = [f"hex-{idx}" for idx in range(len(frame))]
        return frame

    monkeypatch.setattr(lodes, "points_to_hex", _fake_points_to_hex)


def test_geocode_blocks_raises_on_missing_coords() -> None:
    frame = pd.DataFrame({"w_geocode": ["1"], "C000": [10]})
    geocodes = pd.DataFrame({"block_geoid": ["1"], "lat": [None], "lon": [None]})
    ingestor = lodes.LODESIngestor(lodes.LODESConfig(states=["CO"]))
    with pytest.raises(ValueError):
        ingestor.geocode_blocks(frame, geocodes)


def test_allocate_to_hex_groups_jobs() -> None:
    frame = pd.DataFrame({"hex_id": ["a", "a", "b"], "C000": [1, 2, 3]})
    ingestor = lodes.LODESIngestor(lodes.LODESConfig(states=["CO"]))
    allocated = ingestor.allocate_to_hex(frame)
    assert allocated["C000"].sum() == 6


def test_ingest_writes_output(tmp_path, monkeypatch) -> None:
    ingestor = lodes.LODESIngestor(lodes.LODESConfig(states=["CO"]))

    monkeypatch.setattr(ingestor, "fetch", lambda session=None: pd.DataFrame({"w_geocode": ["1"], "C000": [1]}))
    monkeypatch.setattr(
        ingestor,
        "geocode_blocks",
        lambda frame, geocodes: frame.assign(lat=[40.0], lon=[-105.0]),
    )
    output = tmp_path / "jobs.parquet"
    result = ingestor.ingest(pd.DataFrame({"block_geoid": ["1"], "lat": [40.0], "lon": [-105.0]}), output_path=output)
    assert output.exists()
    assert not result.empty
