from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import requests

from ...hex.aggregation import points_to_hex
from ...logging_utils import get_logger
from ...versioning.snapshots import SnapshotRegistry

LOGGER = get_logger("aucs.ingest.parks.ridb")


RIDB_URL = "https://ridb.recreation.gov/api/v1/recareas"


@dataclass
class RIDBConfig:
    api_key: str | None = None
    page_size: int = 200


class RIDBIngestor:
    def __init__(self, config: RIDBConfig | None = None, registry: SnapshotRegistry | None = None):
        self.config = config or RIDBConfig()
        self.registry = registry or SnapshotRegistry(Path("data/snapshots.jsonl"))

    def fetch(self, states: Iterable[str], session: requests.Session | None = None) -> pd.DataFrame:
        session = session or requests.Session()
        records: list[dict[str, object]] = []
        for state in states:
            offset = 0
            while True:
                params = {
                    "limit": self.config.page_size,
                    "offset": offset,
                    "state": state,
                }
                headers = {"apikey": self.config.api_key} if self.config.api_key else None
                LOGGER.info("fetching_ridb", state=state, offset=offset)
                response = session.get(RIDB_URL, params=params, headers=headers, timeout=60)
                response.raise_for_status()
                data = response.json()
                if self.registry.has_changed(f"ridb-{state}", response.content):
                    self.registry.record_snapshot(f"ridb-{state}", response.url, response.content)
                items = data.get("RECDATA", [])
                for item in items:
                    records.append(
                        {
                            "recarea_id": item.get("RecAreaID"),
                            "name": item.get("RecAreaName"),
                            "lat": float(item.get("RecAreaLatitude", 0.0)),
                            "lon": float(item.get("RecAreaLongitude", 0.0)),
                            "states": item.get("RecAreaState"),
                        }
                    )
                if len(items) < self.config.page_size:
                    break
                offset += self.config.page_size
        return pd.DataFrame.from_records(records)

    def index_to_hex(self, frame: pd.DataFrame) -> pd.DataFrame:
        if frame.empty:
            return frame.assign(hex_id=[])
        return points_to_hex(frame, lat_column="lat", lon_column="lon", hex_column="hex_id")

    def ingest(self, states: Iterable[str], output_path: Path = Path("data/processed/recreation_areas.parquet")) -> pd.DataFrame:
        frame = self.fetch(states)
        indexed = self.index_to_hex(frame)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        indexed.to_parquet(output_path)
        return indexed


__all__ = ["RIDBIngestor", "RIDBConfig"]
