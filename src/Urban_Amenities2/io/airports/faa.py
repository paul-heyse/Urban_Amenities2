from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from ...hex.aggregation import points_to_hex


def load_enplanements(path: str | Path) -> pd.DataFrame:
    if str(path).endswith(".csv"):
        return pd.read_csv(path)
    return pd.read_excel(path)


def filter_states(frame: pd.DataFrame, states: Iterable[str]) -> pd.DataFrame:
    states = {state.upper() for state in states}
    if "STATE" in frame.columns:
        return frame[frame["STATE"].str.upper().isin(states)]
    return frame


def compute_weights(frame: pd.DataFrame, column: str = "ENPLANEMENTS") -> pd.DataFrame:
    frame = frame.copy()
    total = frame[column].sum()
    frame["weight"] = frame[column] / total if total else 0.0
    return frame


def index_airports(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.rename(columns={"LAT": "lat", "LON": "lon"})
    frame = points_to_hex(frame, lat_column="lat", lon_column="lon", hex_column="hex_id")
    return frame


def ingest_airports(
    path: str | Path,
    states: Iterable[str],
    output_path: Path = Path("data/processed/airports.parquet"),
) -> pd.DataFrame:
    frame = load_enplanements(path)
    filtered = filter_states(frame, states)
    weighted = compute_weights(filtered)
    indexed = index_airports(weighted)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    indexed.to_parquet(output_path)
    return indexed


__all__ = ["ingest_airports", "load_enplanements", "filter_states", "compute_weights", "index_airports"]
