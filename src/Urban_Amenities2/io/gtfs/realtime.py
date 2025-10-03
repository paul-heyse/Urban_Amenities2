from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import fsspec
import pandas as pd

try:  # pragma: no cover - import guard for optional dependency
    from google.transit import gtfs_realtime_pb2 as feedmessage_pb2
except ModuleNotFoundError:  # pragma: no cover - fallback for test environments
    import json
    from dataclasses import dataclass, field
    from typing import Iterable, Mapping

    @dataclass(slots=True)
    class _StopTimeEvent:
        delay: int | None = None

        def HasField(self, name: str) -> bool:
            return getattr(self, name, None) is not None

        def to_dict(self) -> dict[str, int | None]:
            return {"delay": self.delay}

        @classmethod
        def from_dict(cls, payload: Mapping[str, object]) -> "_StopTimeEvent":
            value = payload.get("delay")
            return cls(delay=int(value) if isinstance(value, int) else None)

    @dataclass(slots=True)
    class _StopTimeUpdate:
        stop_sequence: int | None = None
        departure: _StopTimeEvent = field(default_factory=_StopTimeEvent)
        arrival: _StopTimeEvent = field(default_factory=_StopTimeEvent)

        def HasField(self, name: str) -> bool:
            return getattr(self, name, None) is not None

        def to_dict(self) -> dict[str, object]:
            return {
                "stop_sequence": self.stop_sequence,
                "departure": self.departure.to_dict(),
                "arrival": self.arrival.to_dict(),
            }

        @classmethod
        def from_dict(cls, payload: Mapping[str, object]) -> "_StopTimeUpdate":
            update = cls()
            sequence = payload.get("stop_sequence")
            if isinstance(sequence, int):
                update.stop_sequence = sequence
            departure_payload = payload.get("departure")
            if isinstance(departure_payload, Mapping):
                update.departure = _StopTimeEvent.from_dict(departure_payload)
            arrival_payload = payload.get("arrival")
            if isinstance(arrival_payload, Mapping):
                update.arrival = _StopTimeEvent.from_dict(arrival_payload)
            return update

    @dataclass(slots=True)
    class _TripDescriptor:
        trip_id: str = ""
        route_id: str = ""

        def to_dict(self) -> dict[str, str]:
            return {"trip_id": self.trip_id, "route_id": self.route_id}

        @classmethod
        def from_dict(cls, payload: Mapping[str, object]) -> "_TripDescriptor":
            trip_id = payload.get("trip_id")
            route_id = payload.get("route_id")
            return cls(
                trip_id=str(trip_id) if isinstance(trip_id, str) else "",
                route_id=str(route_id) if isinstance(route_id, str) else "",
            )

    @dataclass(slots=True)
    class _TripUpdate:
        trip: _TripDescriptor = field(default_factory=_TripDescriptor)
        stop_time_update: list[_StopTimeUpdate] = field(default_factory=list)

        def to_dict(self) -> dict[str, object]:
            return {
                "trip": self.trip.to_dict(),
                "stop_time_update": [update.to_dict() for update in self.stop_time_update],
            }

        @classmethod
        def from_dict(cls, payload: Mapping[str, object]) -> "_TripUpdate":
            update = cls()
            trip_payload = payload.get("trip")
            if isinstance(trip_payload, Mapping):
                update.trip = _TripDescriptor.from_dict(trip_payload)
            raw_updates = payload.get("stop_time_update")
            updates: list[_StopTimeUpdate] = []
            if isinstance(raw_updates, Iterable):
                for item in raw_updates:
                    if isinstance(item, Mapping):
                        updates.append(_StopTimeUpdate.from_dict(item))
            update.stop_time_update = updates
            return update

    @dataclass(slots=True)
    class _Entity:
        id: str = ""
        trip_update: _TripUpdate = field(default_factory=_TripUpdate)

        def to_dict(self) -> dict[str, object]:
            return {"id": self.id, "trip_update": self.trip_update.to_dict()}

        @classmethod
        def from_dict(cls, payload: Mapping[str, object]) -> "_Entity":
            entity = cls()
            identifier = payload.get("id")
            if isinstance(identifier, str):
                entity.id = identifier
            trip_payload = payload.get("trip_update")
            if isinstance(trip_payload, Mapping):
                entity.trip_update = _TripUpdate.from_dict(trip_payload)
            return entity

    class _RepeatedContainer(list[_Entity]):
        def add(self) -> _Entity:
            entity = _Entity()
            self.append(entity)
            return entity

    class _FeedMessage:
        def __init__(self) -> None:
            self.entity: _RepeatedContainer = _RepeatedContainer()

        def SerializeToString(self) -> bytes:
            data = {"entity": [entity.to_dict() for entity in self.entity]}
            return json.dumps(data).encode("utf-8")

        def ParseFromString(self, payload: bytes) -> None:
            data = json.loads(payload.decode("utf-8"))
            entities = _RepeatedContainer()
            raw_entities = data.get("entity", [])
            if isinstance(raw_entities, Iterable):
                for entry in raw_entities:
                    if isinstance(entry, Mapping):
                        entities.append(_Entity.from_dict(entry))
            self.entity = entities

    class _FeedModule:
        FeedMessage = _FeedMessage

    feedmessage_pb2 = _FeedModule()

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
        records: list[dict[str, object]] = []
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
        all_trip_updates: list[pd.DataFrame] = []
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
