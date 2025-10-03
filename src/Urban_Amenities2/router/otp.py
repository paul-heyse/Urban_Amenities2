from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime

import requests

from ..logging_utils import get_logger

LOGGER = get_logger("aucs.router.otp")


@dataclass
class OTPConfig:
    base_url: str
    timeout: int = 30


class OTPError(RuntimeError):
    pass


class OTPClient:
    def __init__(self, config: OTPConfig, session: requests.Session | None = None):
        self.config = config
        self.session = session or requests.Session()

    def plan_trip(
        self,
        origin: tuple[float, float],
        destination: tuple[float, float],
        modes: Sequence[str],
        departure: datetime | None = None,
        max_itineraries: int = 3,
    ) -> list[dict[str, object]]:
        query = _build_plan_query()
        departure = departure or datetime.utcnow()
        variables: dict[str, object] = {
            "from": {"lat": origin[1], "lon": origin[0]},
            "to": {"lat": destination[1], "lon": destination[0]},
            "modes": list(modes),
            "date": departure.strftime("%Y-%m-%d"),
            "time": departure.strftime("%H:%M"),
            "numItineraries": max_itineraries,
        }
        response = self.session.post(
            self.config.base_url,
            json={"query": query, "variables": variables},
            timeout=self.config.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, Mapping):
            raise OTPError("OTP response payload is not a mapping")
        if "errors" in payload:
            LOGGER.warning("otp_error", errors=payload["errors"])
            raise OTPError(str(payload["errors"]))
        data = payload.get("data")
        plan = data.get("plan") if isinstance(data, Mapping) else None
        itineraries = plan.get("itineraries") if isinstance(plan, Mapping) else None
        if not isinstance(itineraries, Sequence):
            return []
        return [self._parse_itinerary(itinerary) for itinerary in itineraries if isinstance(itinerary, Mapping)]

    def _parse_itinerary(self, itinerary: Mapping[str, object]) -> dict[str, object]:
        walk = _as_float(itinerary.get("walkTime"))
        transit = _as_float(itinerary.get("transitTime"))
        wait = _as_float(itinerary.get("waitingTime"))
        fare_payload = itinerary.get("fare")
        fare = 0.0
        if isinstance(fare_payload, Mapping):
            fare_amount = (
                fare_payload.get("fare")
                if isinstance(fare_payload.get("fare"), Mapping)
                else None
            )
            if isinstance(fare_amount, Mapping):
                regular = fare_amount.get("regular")
                if isinstance(regular, Mapping):
                    fare = _as_float(regular.get("amount"))
        legs_payload = itinerary.get("legs")
        leg_entries = legs_payload if isinstance(legs_payload, Sequence) else ()
        legs = [
            {
                "mode": leg.get("mode") if isinstance(leg.get("mode"), str) else None,
                "duration": _as_float(leg.get("duration")),
                "distance": _as_float(leg.get("distance")),
                "from": _extract_name(leg.get("from")),
                "to": _extract_name(leg.get("to")),
            }
            for leg in leg_entries
            if isinstance(leg, Mapping)
        ]
        return {
            "duration": _as_float(itinerary.get("duration")),
            "walk_time": walk,
            "transit_time": transit,
            "wait_time": wait,
            "transfers": itinerary.get("transfers", 0),
            "fare": fare,
            "legs": legs,
        }


def _build_plan_query() -> str:
    return """
    query($from: InputCoordinates!, $to: InputCoordinates!, $modes: [TransportMode!], $date: String!, $time: String!, $numItineraries: Int!) {
      plan(
        from: $from,
        to: $to,
        transportModes: $modes,
        date: $date,
        time: $time,
        numItineraries: $numItineraries
      ) {
        itineraries {
          duration
          walkTime
          transitTime
          waitingTime
          transfers
          fare { fare { regular { amount } } }
          legs {
            mode
            duration
            distance
            from { name }
            to { name }
          }
        }
      }
    }
    """


__all__ = ["OTPClient", "OTPConfig", "OTPError"]


def _as_float(value: object) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0


def _extract_name(payload: object) -> str | None:
    if isinstance(payload, Mapping):
        name = payload.get("name")
        if isinstance(name, str):
            return name
    return None
