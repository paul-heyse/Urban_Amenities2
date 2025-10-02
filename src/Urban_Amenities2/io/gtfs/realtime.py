from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import fsspec
import pandas as pd
try:  # pragma: no cover - import guard for optional dependency
    from gtfs_realtime_bindings import feedmessage_pb2  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback for test environments
    import json

    class _StopTimeEvent:
        def __init__(self) -> None:
            self.delay: int | None = None

        def HasField(self, name: str) -> bool:
            return getattr(self, name, None) is not None

        def to_dict(self) -> dict[str, int | None]:
            return {"delay": self.delay}

        @classmethod
        def from_dict(cls, payload: dict[str, int | None]) -> "_StopTimeEvent":
            event = cls()
            event.delay = payload.get("delay")
            return event

    class _StopTimeUpdate:
        def __init__(self) -> None:
            self.stop_sequence: int | None = None
            self.departure = _StopTimeEvent()
            self.arrival = _StopTimeEvent()

        def HasField(self, name: str) -> bool:
            return getattr(self, name, None) is not None

        def to_dict(self) -> dict[str, object]:
            return {
                "stop_sequence": self.stop_sequence,
                "departure": self.departure.to_dict(),
                "arrival": self.arrival.to_dict(),
            }

        @classmethod
        def from_dict(cls, payload: dict[str, object]) -> "_StopTimeUpdate":
            update = cls()
            update.stop_sequence = payload.get("stop_sequence")  # type: ignore[assignment]
            if "departure" in payload:
                update.departure = _StopTimeEvent.from_dict(payload["departure"])  # type: ignore[arg-type]
            if "arrival" in payload:
                update.arrival = _StopTimeEvent.from_dict(payload["arrival"])  # type: ignore[arg-type]
            return update

    class _TripDescriptor:
        def __init__(self) -> None:
            self.trip_id: str = ""
            self.route_id: str = ""

        def to_dict(self) -> dict[str, str]:
            return {"trip_id": self.trip_id, "route_id": self.route_id}

        @classmethod
        def from_dict(cls, payload: dict[str, str]) -> "_TripDescriptor":
            trip = cls()
            trip.trip_id = payload.get("trip_id", "")
            trip.route_id = payload.get("route_id", "")
            return trip

    class _TripUpdate:
        def __init__(self) -> None:
            self.trip = _TripDescriptor()
            self.stop_time_update: list[_StopTimeUpdate] = []

        def to_dict(self) -> dict[str, object]:
            return {
                "trip": self.trip.to_dict(),
                "stop_time_update": [update.to_dict() for update in self.stop_time_update],
            }

        @classmethod
        def from_dict(cls, payload: dict[str, object]) -> "_TripUpdate":
            update = cls()
            if "trip" in payload:
                update.trip = _TripDescriptor.from_dict(payload["trip"])  # type: ignore[arg-type]
            updates = payload.get("stop_time_update", [])  # type: ignore[assignment]
            update.stop_time_update = [
                _StopTimeUpdate.from_dict(item) for item in updates  # type: ignore[list-item]
            ]
            return update

    class _Entity:
        def __init__(self) -> None:
            self.id: str = ""
            self.trip_update = _TripUpdate()

        def to_dict(self) -> dict[str, object]:
            return {"id": self.id, "trip_update": self.trip_update.to_dict()}

        @classmethod
        def from_dict(cls, payload: dict[str, object]) -> "_Entity":
            entity = cls()
            entity.id = payload.get("id", "")
            if "trip_update" in payload:
                entity.trip_update = _TripUpdate.from_dict(payload["trip_update"])  # type: ignore[arg-type]
            return entity

    class _RepeatedContainer(list[_Entity]):
        def add(self) -> _Entity:
            entity = _Entity()
            self.append(entity)
            return entity

    class _FeedMessage:
        def __init__(self) -> None:
            self.entity = _RepeatedContainer()

        def SerializeToString(self) -> bytes:
            data = {"entity": [entity.to_dict() for entity in self.entity]}
            return json.dumps(data).encode("utf-8")

        def ParseFromString(self, payload: bytes) -> None:
            data = json.loads(payload.decode("utf-8"))
            self.entity = _RepeatedContainer()
            for entity_payload in data.get("entity", []):
                self.entity.append(_Entity.from_dict(entity_payload))

    class _FeedModule:
        FeedMessage = _FeedMessage

    feedmessage_pb2 = _FeedModule()  # type: ignore

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
