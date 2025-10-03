from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol, TypedDict, cast

import pandas as pd  # type: ignore[import-untyped]

from .osrm import OSRMLeg, OSRMRoute, OSRMTable
from .otp import OTPClient


class OSRMClientProtocol(Protocol):
    def route(self, coords: Sequence[tuple[float, float]]) -> OSRMRoute | Mapping[str, object]:
        ...

    def table(
        self,
        sources: Sequence[tuple[float, float]],
        destinations: Sequence[tuple[float, float]],
    ) -> OSRMTable | Mapping[str, object]:
        ...


@dataclass
class RouteResult:
    origin: tuple[float, float]
    destination: tuple[float, float]
    mode: str
    period: str | None
    duration_min: float
    distance_m: float | None
    metadata: dict[str, object]


class RoutingAPI:
    def __init__(
        self,
        osrm_clients: Mapping[str, OSRMClientProtocol],
        otp_client: OTPClient | None = None,
    ):
        self.osrm_clients: dict[str, OSRMClientProtocol] = dict(osrm_clients)
        self.otp_client = otp_client

    def route(
        self,
        mode: str,
        origin: tuple[float, float],
        destination: tuple[float, float],
        period: str | None = None,
    ) -> RouteResult:
        if mode in self.osrm_clients:
            result = self.osrm_clients[mode].route([origin, destination])
            osrm_route = _coerce_route(result)
            return RouteResult(
                origin=origin,
                destination=destination,
                mode=mode,
                period=period,
                duration_min=osrm_route.duration / 60.0,
                distance_m=osrm_route.distance,
                metadata=_build_osrm_metadata(mode, osrm_route),
            )
        if mode == "transit" and self.otp_client:
            itineraries = self.otp_client.plan_trip(origin, destination, ["TRANSIT", "WALK"])
            if not itineraries:
                raise ValueError("No itinerary returned")
            best = min(itineraries, key=_duration_key)
            duration_value = best.get("duration")
            duration_minutes = (
                float(duration_value) / 60.0
                if isinstance(duration_value, (int, float))
                else 0.0
            )
            return RouteResult(
                origin=origin,
                destination=destination,
                mode=mode,
                period=period,
                duration_min=duration_minutes,
                distance_m=None,
                metadata=_build_transit_metadata(best),
            )
        raise ValueError(f"Unsupported mode {mode}")

    def matrix(
        self,
        mode: str,
        origins: Sequence[tuple[float, float]],
        destinations: Sequence[tuple[float, float]],
        period: str | None = None,
    ) -> pd.DataFrame:
        if mode not in self.osrm_clients:
            raise ValueError("Matrix computation currently supported for OSRM-backed modes only")
        result = self.osrm_clients[mode].table(origins, destinations)
        table = _coerce_table(result)
        durations = table.durations
        distances = table.distances or []
        records: list[dict[str, object]] = []
        for i, origin in enumerate(origins):
            for j, destination in enumerate(destinations):
                duration_value: float | None = (
                    durations[i][j]
                    if i < len(durations) and j < len(durations[i])
                    else None
                )
                distance_value: float | None = (
                    distances[i][j]
                    if distances and i < len(distances) and j < len(distances[i])
                    else None
                )
                records.append(
                    {
                        "origin_index": i,
                        "destination_index": j,
                        "origin": origin,
                        "destination": destination,
                        "mode": mode,
                        "period": period,
                        "duration_min": duration_value / 60.0 if duration_value is not None else None,
                        "distance_m": distance_value,
                    }
                )
        return pd.DataFrame.from_records(records)


def _build_osrm_metadata(mode: str, route: OSRMRoute) -> dict[str, object]:
    legs = [
        {
            "mode": mode,
            "duration_min": leg.duration / 60.0,
            "distance_m": leg.distance,
        }
        for leg in route.legs
    ]
    return {
        "engine": "osrm",
        "summary": {
            "duration_min": route.duration / 60.0,
            "distance_m": route.distance,
            "leg_count": len(legs),
        },
        "legs": legs,
    }


def _build_transit_metadata(itinerary: Mapping[str, object]) -> dict[str, object]:
    legs_payload = itinerary.get("legs")
    legs_entries = legs_payload if isinstance(legs_payload, Sequence) else ()
    legs: list[dict[str, object]] = []
    for entry in legs_entries:
        if not isinstance(entry, Mapping):
            continue
        legs.append(
            {
                "mode": entry.get("mode") if isinstance(entry.get("mode"), str) else None,
                "duration_min": _coerce_minutes(entry.get("duration")),
                "distance_m": _coerce_float(entry.get("distance")),
                "from": entry.get("from") if isinstance(entry.get("from"), str) else None,
                "to": entry.get("to") if isinstance(entry.get("to"), str) else None,
            }
        )
    walk_minutes = _coerce_minutes(itinerary.get("walk_time"))
    transit_minutes = _coerce_minutes(itinerary.get("transit_time"))
    wait_minutes = _coerce_minutes(itinerary.get("wait_time"))
    return {
        "engine": "otp",
        "summary": {
            "duration_min": _coerce_minutes(itinerary.get("duration")),
            "walk_time_min": walk_minutes,
            "transit_time_min": transit_minutes,
            "wait_time_min": wait_minutes,
            "transfers": itinerary.get("transfers", 0),
            "fare_usd": _coerce_float(itinerary.get("fare")) or 0.0,
        },
        "legs": legs,
    }


def _duration_key(payload: Mapping[str, object]) -> float:
    value = payload.get("duration")
    if isinstance(value, (int, float)):
        return float(value)
    return float("inf")


def _coerce_minutes(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value) / 60.0
    return None


def _coerce_float(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


class _RouteMapping(TypedDict, total=False):
    duration: float
    distance: float | None
    legs: list[dict[str, float | None]]


class _TableMapping(TypedDict, total=False):
    durations: list[list[float | None]]
    distances: list[list[float | None]] | None


def _coerce_route(payload: OSRMRoute | Mapping[str, object]) -> OSRMRoute:
    if isinstance(payload, OSRMRoute):
        return payload
    mapping = cast(_RouteMapping, payload)
    duration = _coerce_float(mapping.get("duration"))
    if duration is None:
        raise ValueError("Route payload missing duration")
    distance = _coerce_float(mapping.get("distance"))
    legs_payload = mapping.get("legs", [])
    legs: list[OSRMLeg] = []
    if isinstance(legs_payload, Sequence):
        for leg_entry in legs_payload:
            if isinstance(leg_entry, Mapping):
                leg_duration = _coerce_float(leg_entry.get("duration"))
                if leg_duration is None:
                    continue
                leg_distance = _coerce_float(leg_entry.get("distance"))
                legs.append(OSRMLeg(duration=leg_duration, distance=leg_distance))
    return OSRMRoute(duration=duration, distance=distance, legs=legs)


def _coerce_table(payload: OSRMTable | Mapping[str, object]) -> OSRMTable:
    if isinstance(payload, OSRMTable):
        return payload
    mapping = cast(_TableMapping, payload)
    durations = mapping.get("durations")
    if not isinstance(durations, list):
        raise ValueError("Table payload missing durations")
    distances = mapping.get("distances")
    return OSRMTable(durations=durations, distances=distances)


__all__ = ["RoutingAPI", "RouteResult"]
