from __future__ import annotations

from pathlib import Path

import pandas as pd

from ...hex.aggregation import points_to_hex


def normalize_registry(frame: pd.DataFrame, state: str) -> pd.DataFrame:
    rename = {
        "provider_id": "facility_id",
        "FacilityID": "facility_id",
        "name": "name",
        "FacilityName": "name",
        "capacity": "capacity",
        "Latitude": "lat",
        "Longitude": "lon",
    }
    frame = frame.rename(columns={k: v for k, v in rename.items() if k in frame.columns})
    columns = {"facility_id", "name", "lat", "lon", "capacity"}
    missing = columns - set(frame.columns)
    if missing:
        raise ValueError(f"Childcare dataset for {state} missing columns {missing}")
    frame["state"] = state
    return frame[list(columns) + ["state"]]


def combine_registries(registries: dict[str, pd.DataFrame]) -> pd.DataFrame:
    frames = [normalize_registry(df, state) for state, df in registries.items()]
    combined = pd.concat(frames, ignore_index=True)
    combined = points_to_hex(combined, lat_column="lat", lon_column="lon", hex_column="hex_id")
    return combined


def ingest_childcare(
    registries: dict[str, str | Path], output_path: Path = Path("data/processed/childcare.parquet")
) -> pd.DataFrame:
    frames = {
        state: (pd.read_parquet(path) if str(path).endswith(".parquet") else pd.read_csv(path))
        for state, path in registries.items()
    }
    combined = combine_registries(frames)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_parquet(output_path)
    return combined


__all__ = ["combine_registries", "ingest_childcare"]
