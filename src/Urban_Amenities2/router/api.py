from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import pandas as pd

from .osrm import OSRMClient
from .otp import OTPClient


@dataclass
class RouteResult:
    origin: Tuple[float, float]
    destination: Tuple[float, float]
    mode: str
    period: Optional[str]
    duration_min: float
    distance_m: Optional[float]
    metadata: dict


class RoutingAPI:
    def __init__(
        self,
        osrm_clients: Dict[str, OSRMClient],
        otp_client: Optional[OTPClient] = None,
    ):
        self.osrm_clients = osrm_clients
        self.otp_client = otp_client

    def route(
        self,
        mode: str,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        period: Optional[str] = None,
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
        origins: Sequence[Tuple[float, float]],
        destinations: Sequence[Tuple[float, float]],
        period: Optional[str] = None,
    ) -> pd.DataFrame:
        if mode not in self.osrm_clients:
            raise ValueError("Matrix computation currently supported for OSRM-backed modes only")
        result = self.osrm_clients[mode].table(origins, destinations)
        durations = result.get("durations", []) or []
        distances = result.get("distances") or []
        records: List[dict[str, object]] = []
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
