from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import fsspec
import pandas as pd
from gtfs_realtime_bindings import feedmessage_pb2

from ...logging_utils import get_logger
from ...versioning.snapshots import SnapshotRegistry
from .registry import Agency

LOGGER = get_logger("aucs.ingest.gtfs.realtime")


@dataclass
class RealtimeConfig:
    on_time_threshold_sec: int = 300


class GTFSRealtimeIngestor:
    def __init__(self, registry: SnapshotRegistry | None = None, config: RealtimeConfig | None = None):
        self.registry = registry or SnapshotRegistry(Path("data/snapshots.jsonl"))
        self.config = config or RealtimeConfig()

    def fetch(self, url: str) -> bytes:
        with fsspec.open(url, mode="rb") as handle:
            data = handle.read()
        if self.registry.has_changed(url, data):
            self.registry.record_snapshot(url, url, data)
        LOGGER.info("fetched_gtfs_rt", url=url, size=len(data))
        return data

    def parse_trip_updates(self, payload: bytes) -> pd.DataFrame:
        feed = feedmessage_pb2.FeedMessage()
        feed.ParseFromString(payload)
        records: List[Dict[str, object]] = []
        for entity in feed.entity:
            if not entity.trip_update.trip.trip_id:
                continue
            trip = entity.trip_update.trip
            for update in entity.trip_update.stop_time_update:
                delay = 0
                if update.HasField("departure") and update.departure.HasField("delay"):
                    delay = update.departure.delay
                elif update.HasField("arrival") and update.arrival.HasField("delay"):
                    delay = update.arrival.delay
                records.append(
                    {
                        "trip_id": trip.trip_id,
                        "route_id": trip.route_id,
                        "delay_sec": delay,
                    }
                )
        return pd.DataFrame.from_records(records)

    def compute_metrics(self, trip_updates: pd.DataFrame) -> pd.DataFrame:
        if trip_updates.empty:
            return pd.DataFrame(columns=["route_id", "avg_delay_sec", "on_time_share"])
        grouped = trip_updates.groupby("route_id")
        records = []
        for route_id, group in grouped:
            avg_delay = group["delay_sec"].mean()
            on_time = (group["delay_sec"].abs() <= self.config.on_time_threshold_sec).mean()
            records.append({"route_id": route_id, "avg_delay_sec": avg_delay, "on_time_share": on_time})
        return pd.DataFrame.from_records(records)

    def ingest(self, agency: Agency, output_path: Path = Path("data/processed/gtfs_reliability.parquet")) -> Path:
        all_trip_updates: List[pd.DataFrame] = []
        for url in agency.realtime_urls:
            payload = self.fetch(url)
            updates = self.parse_trip_updates(payload)
            all_trip_updates.append(updates)
        if all_trip_updates:
            combined = pd.concat(all_trip_updates, ignore_index=True)
        else:
            combined = pd.DataFrame(columns=["route_id", "delay_sec"])
        metrics = self.compute_metrics(combined)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        metrics.to_parquet(output_path)
        return output_path


__all__ = ["GTFSRealtimeIngestor", "RealtimeConfig"]
