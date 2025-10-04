from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass

import requests

from ..logging_utils import get_logger

LOGGER = get_logger("aucs.router.osrm")


@dataclass(slots=True)
class OSRMConfig:
    base_url: str
    profile: str = "car"
    timeout: int = 30
    max_matrix: int = 100


class _MappingPayload(Mapping[str, object]):
    __slots__ = ()

    def as_dict(self) -> dict[str, object]:
        raise NotImplementedError

    def __getitem__(self, key: str) -> object:
        return self.as_dict()[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.as_dict())

    def __len__(self) -> int:
        return len(self.as_dict())

    def keys(self) -> list[str]:
        return list(self.as_dict().keys())

    def items(self) -> list[tuple[str, object]]:
        return list(self.as_dict().items())


@dataclass(slots=True)
class OSRMLeg(_MappingPayload):
    duration: float
    distance: float | None

    def as_dict(self) -> dict[str, float | None]:
        return {
            "duration": self.duration,
            "distance": self.distance,
        }


@dataclass(slots=True)
class OSRMRoute(_MappingPayload):
    duration: float
    distance: float | None
    legs: list[OSRMLeg]

    def as_dict(self) -> dict[str, object]:
        return {
            "duration": self.duration,
            "distance": self.distance,
            "legs": [leg.as_dict() for leg in self.legs],
        }


@dataclass(slots=True)
class OSRMTable(_MappingPayload):
    durations: list[list[float | None]]
    distances: list[list[float | None]] | None

    def as_dict(self) -> dict[str, object]:
        return {
            "durations": self.durations,
            "distances": self.distances,
        }


class RoutingError(RuntimeError):
    """Raised when routing fails."""


class OSRMClient:
    def __init__(self, config: OSRMConfig, session: requests.Session | None = None):
        self.config = config
        self.session = session or requests.Session()

    def _format_coords(self, coords: Sequence[tuple[float, float]]) -> str:
        return ";".join(f"{lon},{lat}" for lon, lat in coords)

    def _request(
        self, path: str, params: Mapping[str, str | int | float] | None = None
    ) -> dict[str, object]:
        url = f"{self.config.base_url.rstrip('/')}/{path}"
        response = self.session.get(url, params=params, timeout=self.config.timeout)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise RoutingError("OSRM response payload is not a JSON object")
        code = payload.get("code")
        if code and code != "Ok":
            LOGGER.warning("osrm_error", path=path, code=code, message=payload.get("message"))
            raise RoutingError(payload.get("message", "OSRM request failed"))
        return payload

    def route(self, coords: Sequence[tuple[float, float]]) -> OSRMRoute:
        if len(coords) < 2:
            raise ValueError("At least two coordinates required")
        path = f"route/v1/{self.config.profile}/{self._format_coords(coords)}"
        params = {"annotations": "duration,distance", "overview": "false"}
        payload = self._request(path, params=params)
        routes = payload.get("routes", [])
        if not isinstance(routes, Sequence):
            raise RoutingError("No route found")
        if not routes:
            raise RoutingError("No route found")
        route_payload = routes[0]
        if not isinstance(route_payload, Mapping):
            raise RoutingError("Route payload malformed")
        duration = _coerce_float(route_payload.get("duration"))
        if duration is None:
            raise RoutingError("Route duration missing from OSRM payload")
        distance = _coerce_float(route_payload.get("distance"))
        legs = _parse_legs(route_payload.get("legs"))
        return OSRMRoute(duration=duration, distance=distance, legs=legs)

    def table(
        self,
        sources: Sequence[tuple[float, float]],
        destinations: Sequence[tuple[float, float]] | None = None,
    ) -> OSRMTable:
        destinations = destinations or sources
        if len(sources) > self.config.max_matrix or len(destinations) > self.config.max_matrix:
            return self._table_batched(sources, destinations)
        coords = list(sources) + list(destinations)
        path = f"table/v1/{self.config.profile}/{self._format_coords(coords)}"
        source_indexes = list(range(len(sources)))
        dest_indexes = list(range(len(sources), len(coords)))
        params = {
            "sources": ";".join(map(str, source_indexes)),
            "destinations": ";".join(map(str, dest_indexes)),
        }
        payload = self._request(path, params=params)
        durations = _parse_matrix(payload.get("durations"))
        if durations is None:
            raise RoutingError("Duration matrix missing from OSRM table response")
        distances = _parse_matrix(payload.get("distances"))
        return OSRMTable(durations=durations, distances=distances)

    def _table_batched(
        self,
        sources: Sequence[tuple[float, float]],
        destinations: Sequence[tuple[float, float]],
    ) -> OSRMTable:
        durations: list[list[float | None]] = []
        distances: list[list[float | None]] = []
        for start in range(0, len(sources), self.config.max_matrix):
            batch_sources = sources[start : start + self.config.max_matrix]
            row_durations: list[list[list[float | None]]] = []
            row_distances: list[list[list[float | None]]] = []
            for dest_start in range(0, len(destinations), self.config.max_matrix):
                batch_destinations = destinations[dest_start : dest_start + self.config.max_matrix]
                result = self.table(batch_sources, batch_destinations)
                row_durations.append(result.durations)
                if result.distances is not None:
                    row_distances.append(result.distances)
            durations.extend(_concatenate_rows(row_durations))
            if row_distances:
                distances.extend(_concatenate_rows(row_distances))
        distance_matrix: list[list[float | None]] | None = distances or None
        return OSRMTable(durations=durations, distances=distance_matrix)


def _concatenate_rows(rows: Sequence[Sequence[Sequence[float | None]]]) -> list[list[float | None]]:
    if not rows:
        return []
    expected_rows = len(rows[0])
    result: list[list[float | None]] = []
    for row_idx in range(expected_rows):
        combined: list[float | None] = []
        for block in rows:
            if len(block) != expected_rows:
                raise RoutingError("Inconsistent OSRM table row block size")
            combined.extend(block[row_idx])
        result.append(combined)
    return result


def _coerce_float(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _parse_legs(payload: object) -> list[OSRMLeg]:
    if not isinstance(payload, Sequence):
        return []
    legs: list[OSRMLeg] = []
    for entry in payload:
        if not isinstance(entry, Mapping):
            continue
        duration = _coerce_float(entry.get("duration"))
        distance = _coerce_float(entry.get("distance"))
        if duration is not None:
            legs.append(OSRMLeg(duration=duration, distance=distance))
    return legs


def _parse_matrix(payload: object) -> list[list[float | None]] | None:
    if payload is None:
        return None
    if not isinstance(payload, Sequence):
        return None
    matrix: list[list[float | None]] = []
    for row in payload:
        if not isinstance(row, Sequence):
            return None
        parsed_row: list[float | None] = []
        for value in row:
            if isinstance(value, (int, float)):
                parsed_row.append(float(value))
            elif value is None:
                parsed_row.append(None)
            else:
                raise RoutingError("Matrix contains non-numeric value")
        matrix.append(parsed_row)
    return matrix


__all__ = [
    "OSRMClient",
    "OSRMConfig",
    "OSRMLeg",
    "OSRMRoute",
    "OSRMTable",
    "RoutingError",
]
