from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

import pandas as pd
import requests

from ...hex.core import latlon_to_hex
from ...logging_utils import get_logger
from ...versioning.snapshots import SnapshotRegistry

LOGGER = get_logger("aucs.ingest.climate.noaa")

NOAA_URL = "https://www.ncei.noaa.gov/access/services/data/v1"


@dataclass
class NOAAConfig:
    dataset: str = "normals-monthly-1991-2020"
    elements: Sequence[str] = ("MLY-TAVG-NORMAL", "MLY-PRCP-PRB", "MLY-WSF2-NORMAL")
    units: str = "metric"
    token: Optional[str] = None


class NoaaNormalsIngestor:
    def __init__(self, config: NOAAConfig | None = None, registry: SnapshotRegistry | None = None):
        self.config = config or NOAAConfig()
        self.registry = registry or SnapshotRegistry(Path("data/snapshots.jsonl"))

    def fetch(self, state: str, session: Optional[requests.Session] = None) -> pd.DataFrame:
        session = session or requests.Session()
        params = {
            "dataset": self.config.dataset,
            "dataTypes": ",".join(self.config.elements),
            "format": "json",
            "state": state,
            "includeStationName": "1",
            "units": self.config.units,
        }
        headers = {"token": self.config.token} if self.config.token else None
        LOGGER.info("fetching_noaa_normals", state=state)
        response = session.get(NOAA_URL, params=params, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list):
            msg = f"Unexpected NOAA response format for state {state}"
            raise ValueError(msg)
        frame = pd.DataFrame(data)
        frame["state"] = state
        if self.registry.has_changed(f"noaa-{state}", response.content):
            self.registry.record_snapshot(f"noaa-{state}", response.url, response.content)
        return self._normalise_columns(frame)

    def _normalise_columns(self, frame: pd.DataFrame) -> pd.DataFrame:
        column_map = {
            "MLY-TAVG-NORMAL": "tavg_c",
            "MLY-PRCP-PRB": "precip_probability",
            "MLY-WSF2-NORMAL": "wind_mps",
        }
        rename = {key: value for key, value in column_map.items() if key in frame.columns}
        normalised = frame.rename(columns=rename)
        normalised["month"] = normalised["month"].astype(int)
        if "precip_probability" in normalised.columns:
            normalised["precip_probability"] = normalised["precip_probability"].astype(float) / 100.0
        if "tavg_c" in normalised.columns:
            normalised["tavg_c"] = normalised["tavg_c"].astype(float)
        if "wind_mps" in normalised.columns:
            normalised["wind_mps"] = normalised["wind_mps"].astype(float)
        return normalised

    def fetch_states(self, states: Iterable[str], session: Optional[requests.Session] = None) -> pd.DataFrame:
        frames = [self.fetch(state, session=session) for state in states]
        return pd.concat(frames, ignore_index=True)

    def interpolate_to_hex(self, frame: pd.DataFrame, resolution: int = 9) -> pd.DataFrame:
        if frame.empty:
            return pd.DataFrame(columns=["hex_id", "month", "tavg_c", "precip_probability", "wind_mps"])
        frame = frame.copy()
        frame["hex_id"] = [latlon_to_hex(row["latitude"], row["longitude"], resolution) for _, row in frame.iterrows()]
        return frame

    def compute_comfort_index(self, frame: pd.DataFrame) -> pd.DataFrame:
        if frame.empty:
            return pd.DataFrame(columns=["hex_id", "month", "sigma_out"])
        records: List[dict[str, object]] = []
        for (hex_id, month), group in frame.groupby(["hex_id", "month"]):
            temp = group["tavg_c"].mean() if "tavg_c" in group else None
            precip_prob = group["precip_probability"].mean() if "precip_probability" in group else None
            wind = group["wind_mps"].mean() if "wind_mps" in group else None
            sigma = _comfortable_fraction(temp, precip_prob, wind)
            records.append({"hex_id": hex_id, "month": month, "sigma_out": sigma})
        return pd.DataFrame.from_records(records)

    def ingest(
        self,
        states: Iterable[str],
        session: Optional[requests.Session] = None,
        output_path: Path = Path("data/processed/climate_comfort.parquet"),
    ) -> pd.DataFrame:
        frame = self.fetch_states(states, session=session)
        interpolated = self.interpolate_to_hex(frame)
        comfort = self.compute_comfort_index(interpolated)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        comfort.to_parquet(output_path)
        return comfort


def _comfortable_fraction(temp: Optional[float], precip_prob: Optional[float], wind: Optional[float]) -> float:
    if temp is None:
        return 1.0
    temp_ok = 1.0 if 10.0 <= temp <= 27.0 else 0.0
    if temp_ok == 0.0:
        return 0.0
    precip_component = 1.0 if precip_prob is None else max(0.0, 1.0 - (precip_prob / 0.4))
    wind_component = 1.0 if wind is None else max(0.0, 1.0 - (wind / 8.0))
    sigma = temp_ok * min(1.0, precip_component) * min(1.0, wind_component)
    return max(0.0, min(1.0, sigma))


__all__ = ["NoaaNormalsIngestor", "NOAAConfig"]
