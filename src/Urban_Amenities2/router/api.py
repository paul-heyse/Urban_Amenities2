from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd

from .osrm import OSRMClient
from .otp import OTPClient


@dataclass
class RouteResult:
    origin: tuple[float, float]
    destination: tuple[float, float]
    mode: str
    period: str | None
    duration_min: float
    distance_m: float | None
    metadata: dict


class RoutingAPI:
    def __init__(
        self,
        osrm_clients: dict[str, OSRMClient],
        otp_client: OTPClient | None = None,
    ):
        self.osrm_clients = osrm_clients
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
                duration_min=result["duration"] / 60.0,
                distance_m=result.get("distance"),
                metadata={"legs": result.get("legs", [])},
            )
        if mode == "transit" and self.otp_client:
            itineraries = self.otp_client.plan_trip(origin, destination, ["TRANSIT", "WALK"])
            if not itineraries:
                raise ValueError("No itinerary returned")
            best = min(itineraries, key=lambda item: item.get("duration", float("inf")))
            return RouteResult(
                origin=origin,
                destination=destination,
                mode=mode,
                period=period,
                duration_min=best.get("duration", 0) / 60.0,
                distance_m=None,
                metadata=best,
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
        durations = result.get("durations", []) or []
        distances = result.get("distances") or []
        records: list[dict[str, object]] = []
        for i, origin in enumerate(origins):
            for j, destination in enumerate(destinations):
                duration = durations[i][j] if i < len(durations) and j < len(durations[i]) else None
                distance = distances[i][j] if distances and i < len(distances) and j < len(distances[i]) else None
                records.append(
                    {
                        "origin_index": i,
                        "destination_index": j,
                        "origin": origin,
                        "destination": destination,
                        "mode": mode,
                        "period": period,
                        "duration_min": duration / 60.0 if duration is not None else None,
                        "distance_m": distance,
                    }
                )
        return pd.DataFrame.from_records(records)


__all__ = ["RoutingAPI", "RouteResult"]
