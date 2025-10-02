from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

from ...hex.aggregation import points_to_hex
from ...logging_utils import get_logger
from ...versioning.snapshots import SnapshotRegistry

LOGGER = get_logger("aucs.ingest.jobs.lodes")

LODES_URL_TEMPLATE = "https://lehd.ces.census.gov/data/lodes/LODES8/{state}/wac/{state}_wac_S000_JT00_2020.csv.gz"


@dataclass
class LODESConfig:
    states: Iterable[str]


class LODESIngestor:
    def __init__(self, config: LODESConfig, registry: SnapshotRegistry | None = None):
        self.config = config
        self.registry = registry or SnapshotRegistry(Path("data/snapshots.jsonl"))

    def fetch_state(self, state: str, session=None) -> pd.DataFrame:
        import fsspec

        state = state.lower()
        url = LODES_URL_TEMPLATE.format(state=state)
        LOGGER.info("fetching_lodes", state=state, url=url)
        with fsspec.open(url, mode="rb") as handle:
            data = handle.read()
        if self.registry.has_changed(f"lodes-{state}", data):
            self.registry.record_snapshot(f"lodes-{state}", url, data)
        frame = pd.read_csv(io.BytesIO(data), compression="gzip")
        frame["state"] = state.upper()
        return frame

    def fetch(self, session=None) -> pd.DataFrame:
        frames = [self.fetch_state(state, session=session) for state in self.config.states]
        return pd.concat(frames, ignore_index=True)

    def geocode_blocks(self, frame: pd.DataFrame, geocodes: pd.DataFrame) -> pd.DataFrame:
        merged = frame.merge(geocodes, left_on="w_geocode", right_on="block_geoid", how="left")
        if merged[["lat", "lon"]].isna().any().any():
            missing = merged[merged["lat"].isna()]["w_geocode"].unique().tolist()
            raise ValueError(f"Missing geocodes for blocks: {missing[:5]}")
        return merged

    def allocate_to_hex(self, frame: pd.DataFrame) -> pd.DataFrame:
        points = points_to_hex(frame.rename(columns={"lat": "lat", "lon": "lon"}), hex_column="hex_id")
        job_columns = [col for col in frame.columns if col.startswith("CNS") or col in {"C000", "CNS01"}]
        aggregated = points.groupby("hex_id")[job_columns].sum().reset_index()
        return aggregated

    def ingest(
        self,
        geocodes: pd.DataFrame,
        session=None,
        output_path: Path = Path("data/processed/jobs_by_hex.parquet"),
    ) -> pd.DataFrame:
        frame = self.fetch(session=session)
        geocoded = self.geocode_blocks(frame, geocodes)
        allocated = self.allocate_to_hex(geocoded)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        allocated.to_parquet(output_path)
        return allocated


__all__ = ["LODESIngestor", "LODESConfig"]
