from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import requests

from ..logging_utils import get_logger

LOGGER = get_logger("aucs.router.osrm")


@dataclass
class OSRMConfig:
    base_url: str
    profile: str = "car"
    timeout: int = 30
    max_matrix: int = 100


class RoutingError(RuntimeError):
    """Raised when routing fails."""


class OSRMClient:
    def __init__(self, config: OSRMConfig, session: requests.Session | None = None):
        self.config = config
        self.session = session or requests.Session()

    def _format_coords(self, coords: Sequence[tuple[float, float]]) -> str:
        return ";".join(f"{lon},{lat}" for lon, lat in coords)

    def _request(self, path: str, params: dict[str, object] | None = None) -> dict:
        url = f"{self.config.base_url.rstrip('/')}/{path}"
        response = self.session.get(url, params=params, timeout=self.config.timeout)
        response.raise_for_status()
        payload = response.json()
        code = payload.get("code")
        if code and code != "Ok":
            LOGGER.warning("osrm_error", path=path, code=code, message=payload.get("message"))
            raise RoutingError(payload.get("message", "OSRM request failed"))
        return payload

    def route(self, coords: Sequence[tuple[float, float]]):
        if len(coords) < 2:
            raise ValueError("At least two coordinates required")
        path = f"route/v1/{self.config.profile}/{self._format_coords(coords)}"
        payload = self._request(path, params={"annotations": "duration,distance", "overview": "false"})
        routes = payload.get("routes", [])
        if not routes:
            raise RoutingError("No route found")
        route = routes[0]
        return {
            "duration": route.get("duration"),
            "distance": route.get("distance"),
            "legs": route.get("legs", []),
        }

    def table(
        self,
        sources: Sequence[tuple[float, float]],
        destinations: Sequence[tuple[float, float]] | None = None,
    ) -> dict:
        destinations = destinations or sources
        if len(sources) > self.config.max_matrix or len(destinations) > self.config.max_matrix:
            return self._table_batched(sources, destinations)
        coords = list(sources) + list(destinations)
        path = f"table/v1/{self.config.profile}/{self._format_coords(coords)}"
        source_indexes = list(range(len(sources)))
        dest_indexes = list(range(len(sources), len(coords)))
        params = {"sources": ";".join(map(str, source_indexes)), "destinations": ";".join(map(str, dest_indexes))}
        payload = self._request(path, params=params)
        return {
            "durations": payload.get("durations"),
            "distances": payload.get("distances"),
        }

    def _table_batched(
        self,
        sources: Sequence[tuple[float, float]],
        destinations: Sequence[tuple[float, float]],
    ) -> dict:
        durations: list[list[float]] = []
        distances: list[list[float]] = []
        for start in range(0, len(sources), self.config.max_matrix):
            batch_sources = sources[start : start + self.config.max_matrix]
            row_durations: list[list[float]] = []
            row_distances: list[list[float]] = []
            for dest_start in range(0, len(destinations), self.config.max_matrix):
                batch_destinations = destinations[dest_start : dest_start + self.config.max_matrix]
                result = self.table(batch_sources, batch_destinations)
                row_durations.append(result.get("durations", []))
                if "distances" in result:
                    row_distances.append(result["distances"])
            durations.extend(_concatenate_rows(row_durations))
            if row_distances:
                distances.extend(_concatenate_rows(row_distances))
        return {"durations": durations, "distances": distances or None}


def _concatenate_rows(rows: list[list[list[float]]]) -> list[list[float]]:
    if not rows:
        return []
    result: list[list[float]] = []
    for row_idx in range(len(rows[0])):
        combined: list[float] = []
        for block in rows:
            combined.extend(block[row_idx])
        result.append(combined)
    return result


__all__ = ["OSRMClient", "OSRMConfig", "RoutingError"]
