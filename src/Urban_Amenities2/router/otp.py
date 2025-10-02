from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Sequence

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
    def __init__(self, config: OTPConfig, session: Optional[requests.Session] = None):
        self.config = config
        self.session = session or requests.Session()

    def plan_trip(
        self,
        origin: tuple[float, float],
        destination: tuple[float, float],
        modes: Sequence[str],
        departure: Optional[datetime] = None,
        max_itineraries: int = 3,
    ) -> List[dict[str, object]]:
        query = _build_plan_query()
        departure = departure or datetime.utcnow()
        variables = {
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
        if "errors" in payload:
            LOGGER.warning("otp_error", errors=payload["errors"])
            raise OTPError(str(payload["errors"]))
        itineraries = payload.get("data", {}).get("plan", {}).get("itineraries", [])
        return [self._parse_itinerary(itinerary) for itinerary in itineraries]

    def _parse_itinerary(self, itinerary: dict) -> dict[str, object]:
        walk = itinerary.get("walkTime", 0)
        transit = itinerary.get("transitTime", 0)
        wait = itinerary.get("waitingTime", 0)
        fare = itinerary.get("fare", {}).get("fare", {}).get("regular", {}).get("amount", 0)
        legs = [
            {
                "mode": leg.get("mode"),
                "duration": leg.get("duration"),
                "distance": leg.get("distance"),
                "from": leg.get("from", {}).get("name"),
                "to": leg.get("to", {}).get("name"),
            }
            for leg in itinerary.get("legs", [])
        ]
        return {
            "duration": itinerary.get("duration"),
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
