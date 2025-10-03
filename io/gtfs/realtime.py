from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover
    from google.transit import gtfs_realtime_pb2

try:  # pragma: no cover - import guard for optional dependency
    from google.transit import gtfs_realtime_pb2
except ModuleNotFoundError:  # pragma: no cover - fallback for test environments
    import json

    @dataclass
    class _StopTimeEvent:
        delay: int | None = None

        @classmethod
        def from_dict(cls, payload: dict[str, Any]) -> _StopTimeEvent:
            value = payload.get("delay")
            delay = int(value) if isinstance(value, (int, float)) else None
            return cls(delay=delay)

    @dataclass
    class _StopTimeUpdate:
        stop_sequence: int | None = None
        departure: _StopTimeEvent | None = None
        arrival: _StopTimeEvent | None = None

        @classmethod
        def from_dict(cls, payload: dict[str, Any]) -> _StopTimeUpdate:
            stop = payload.get("stop_sequence")
            departure_payload = payload.get("departure")
            arrival_payload = payload.get("arrival")
            return cls(
                stop_sequence=int(stop) if isinstance(stop, (int, float)) else None,
                departure=(
                    _StopTimeEvent.from_dict(departure_payload)
                    if isinstance(departure_payload, dict)
                    else None
                ),
                arrival=(
                    _StopTimeEvent.from_dict(arrival_payload)
                    if isinstance(arrival_payload, dict)
                    else None
                ),
            )

    @dataclass
    class _TripDescriptor:
        trip_id: str = ""

        @classmethod
        def from_dict(cls, payload: dict[str, Any]) -> _TripDescriptor:
            trip_id = payload.get("trip_id")
            return cls(trip_id=str(trip_id) if trip_id is not None else "")

    @dataclass
    class _TripUpdate:
        trip: _TripDescriptor | None = None
        stop_time_update: list[_StopTimeUpdate] | None = None

        @classmethod
        def from_dict(cls, payload: dict[str, Any]) -> _TripUpdate:
            trip_payload = payload.get("trip")
            updates_payload = payload.get("stop_time_update")
            updates: list[_StopTimeUpdate] | None = None
            if isinstance(updates_payload, list):
                updates = [
                    _StopTimeUpdate.from_dict(item)
                    for item in updates_payload
                    if isinstance(item, dict)
                ]
            return cls(
                trip=(
                    _TripDescriptor.from_dict(trip_payload)
                    if isinstance(trip_payload, dict)
                    else None
                ),
                stop_time_update=updates,
            )

    @dataclass
    class _Entity:
        id: str = ""
        trip_update: _TripUpdate | None = None

        @classmethod
        def from_dict(cls, payload: dict[str, Any]) -> _Entity:
            identifier = payload.get("id")
            trip_update_payload = payload.get("trip_update")
            return cls(
                id=str(identifier) if identifier is not None else "",
                trip_update=(
                    _TripUpdate.from_dict(trip_update_payload)
                    if isinstance(trip_update_payload, dict)
                    else None
                ),
            )

    @dataclass
    class _FeedMessage:
        entity: list[_Entity]

        @classmethod
        def FromString(cls, payload: bytes) -> _FeedMessage:  # pragma: no cover - compatibility
            parsed = json.loads(payload.decode("utf-8"))
            entities_payload = parsed.get("entity", [])
            entities = [
                _Entity.from_dict(item) for item in entities_payload if isinstance(item, dict)
            ]
            return cls(entity=entities)

    class _FeedModule:
        FeedMessage = _FeedMessage

    gtfs_realtime_pb2 = _FeedModule()
