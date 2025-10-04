from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ...hex.aggregation import points_to_hex
from ...logging_utils import get_logger

LOGGER = get_logger("aucs.ingest.education.nces")


REQUIRED_COLUMNS = {
    "school_id",
    "name",
    "level",
    "enrollment",
    "student_teacher_ratio",
    "lat",
    "lon",
}


def _normalise_frame(frame: pd.DataFrame, source: str) -> pd.DataFrame:
    rename_map = {
        "NCESSCH": "school_id",
        "SCH_NAME": "name",
        "LAT": "lat",
        "LON": "lon",
        "LEVEL": "level",
        "ENR_TOTAL": "enrollment",
        "TOTFTE": "teachers_fte",
        "PUPTCH": "student_teacher_ratio",
    }
    frame = frame.rename(
        columns={key: value for key, value in rename_map.items() if key in frame.columns}
    )
    if "student_teacher_ratio" not in frame.columns and {"enrollment", "teachers_fte"}.issubset(
        frame.columns
    ):
        teachers = frame["teachers_fte"].replace({0: pd.NA})
        ratio = frame["enrollment"] / teachers
        frame["student_teacher_ratio"] = ratio.replace([np.inf, -np.inf], pd.NA)
    frame["source"] = source
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns {missing} in NCES dataset {source}")
    columns = list(REQUIRED_COLUMNS) + ["source"]
    return frame[columns]


def prepare_schools(public: pd.DataFrame, private: pd.DataFrame) -> pd.DataFrame:
    frames = [_normalise_frame(public, "public"), _normalise_frame(private, "private")]
    combined = pd.concat(frames, ignore_index=True)
    combined = points_to_hex(combined, lat_column="lat", lon_column="lon", hex_column="hex_id")
    return combined


def ingest_schools(
    public_path: str | Path,
    private_path: str | Path,
    output_path: Path = Path("data/processed/schools.parquet"),
) -> pd.DataFrame:
    public = (
        pd.read_parquet(public_path)
        if str(public_path).endswith(".parquet")
        else pd.read_csv(public_path)
    )
    private = (
        pd.read_parquet(private_path)
        if str(private_path).endswith(".parquet")
        else pd.read_csv(private_path)
    )
    combined = prepare_schools(public, private)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_parquet(output_path)
    return combined


__all__ = ["prepare_schools", "ingest_schools"]
