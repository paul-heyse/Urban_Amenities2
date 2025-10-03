from __future__ import annotations

from pathlib import Path

import pandas as pd

from ...hex.aggregation import points_to_hex
from ...logging_utils import get_logger

LOGGER = get_logger("aucs.ingest.education.ipeds")


CARNEGIE_WEIGHTS: dict[str, float] = {
    "R1": 1.0,
    "R2": 0.9,
    "Doctoral": 0.8,
    "Master's": 0.6,
    "Baccalaureate": 0.5,
    "Associate": 0.4,
}


def compute_weights(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    def _weight(value: str) -> float:
        for key, weight in CARNEGIE_WEIGHTS.items():
            if value and key.lower() in value.lower():
                return weight
        return 0.3

    frame["q_u"] = frame["carnegie"].apply(_weight)
    return frame


def prepare_universities(directory: pd.DataFrame, carnegie: pd.DataFrame) -> pd.DataFrame:
    frame = directory.merge(carnegie, on="unitid", how="left", suffixes=("", "_carnegie"))
    frame = compute_weights(frame)
    frame = points_to_hex(
        frame.rename(columns={"latitude": "lat", "longitude": "lon"}),
        lat_column="lat",
        lon_column="lon",
        hex_column="hex_id",
    )
    return frame


def ingest_universities(
    directory_path: str | Path,
    carnegie_path: str | Path,
    output_path: Path = Path("data/processed/universities.parquet"),
) -> pd.DataFrame:
    directory = pd.read_parquet(directory_path) if str(directory_path).endswith(".parquet") else pd.read_csv(directory_path)
    carnegie = pd.read_parquet(carnegie_path) if str(carnegie_path).endswith(".parquet") else pd.read_csv(carnegie_path)
    prepared = prepare_universities(directory, carnegie)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prepared.to_parquet(output_path)
    return prepared


__all__ = ["prepare_universities", "ingest_universities", "compute_weights"]
