from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol

import pandas as pd  # type: ignore[import-untyped]

from .osrm import OSRMRoute, OSRMTable
from .otp import OTPClient


class OSRMClientProtocol(Protocol):
    def route(self, coords: Sequence[tuple[float, float]]) -> OSRMRoute:
        ...

    def table(
        self,
        sources: Sequence[tuple[float, float]],
        destinations: Sequence[tuple[float, float]],
    ) -> OSRMTable:
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
            return RouteResult(
                origin=origin,
                destination=destination,
                mode=mode,
                period=period,
                duration_min=result.duration / 60.0,
                distance_m=result.distance,
                metadata={
                    "legs": [
                        {"duration": leg.duration, "distance": leg.distance}
                        for leg in result.legs
                    ]
                },
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
                metadata=dict(best),
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
        durations = result.durations
        distances = result.distances or []
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


def _duration_key(payload: Mapping[str, object]) -> float:
    value = payload.get("duration")
    if isinstance(value, (int, float)):
        return float(value)
    return float("inf")


__all__ = ["RoutingAPI", "RouteResult"]
