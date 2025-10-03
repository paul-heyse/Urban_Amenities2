from __future__ import annotations

from collections import OrderedDict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd
from pyproj import Transformer
from rtree.index import Index
from shapely.geometry import Point
from shapely.ops import transform

from ..config.params import CorridorConfig as CorridorParams
from ..logging_utils import get_logger
from ..router.otp import OTPClient

LOGGER = get_logger("aucs.cte")
WALKING_SPEED_M_PER_MIN = 80.0  # ≈ 3 mph


@dataclass(slots=True)
class TransitPath:
    """Represents a feasible transit path between a hex and a hub."""

    hex_id: str
    hub_id: str
    path_index: int
    stops: list[str]
    duration_minutes: float
    transfers: int
    score: float


class TransitPathIdentifier:
    """Identify top transit paths per hex using an OTP client."""

    def __init__(
        self,
        otp_client: OTPClient,
        config: CorridorParams,
        modes: Sequence[str] | None = None,
    ) -> None:
        self._otp = otp_client
        self._config = config
        self._modes = list(modes or ["TRANSIT"])
        self._cache: OrderedDict[tuple[str, str], list[TransitPath]] = OrderedDict()

    def identify_paths(
        self,
        hex_id: str,
        origin: tuple[float, float],
        metro: str,
    ) -> list[TransitPath]:
        hubs = self._config.major_hubs.get(metro.lower(), [])
        if not hubs:
            LOGGER.warning("cte_no_hubs", metro=metro)
            return []
        paths: list[TransitPath] = []
        for hub in hubs:
            key = (hex_id, hub.id)
            cached = self._cache.get(key)
            if cached is not None:
                paths.extend(cached)
                continue
            itineraries = self._otp.plan_trip(
                origin=origin,
                destination=(hub.lon, hub.lat),
                modes=self._modes,
                max_itineraries=max(self._config.max_paths, 2),
            )
            hub_paths = self._select_paths(hex_id, hub.id, itineraries)
            self._store_cache(key, hub_paths)
            paths.extend(hub_paths)
        paths.sort(key=lambda item: item.score, reverse=True)
        selected = paths[: self._config.max_paths]
        LOGGER.debug(
            "cte_paths",
            hex_id=hex_id,
            metro=metro,
            candidates=len(paths),
            selected=len(selected),
        )
        return selected

    def coverage(self, hex_ids: Sequence[str], path_map: Mapping[str, list[TransitPath]]) -> float:
        if not hex_ids:
            return 0.0
        covered = sum(1 for hex_id in hex_ids if path_map.get(hex_id))
        return covered / len(hex_ids)

    def _select_paths(
        self,
        hex_id: str,
        hub_id: str,
        itineraries: Iterable[dict[str, object]],
    ) -> list[TransitPath]:
        paths: list[TransitPath] = []
        for _idx, itinerary in enumerate(itineraries):
            legs = itinerary.get("legs", [])
            stops = self._extract_stops(legs)
            if len(stops) < self._config.min_stop_count:
                continue
            duration = float(itinerary.get("duration", 0.0)) / 60.0
            transfers = int(itinerary.get("transfers", 0))
            if duration <= 0:
                continue
            directness = 1.0 / (1.0 + transfers)
            score = directness / duration
            paths.append(
                TransitPath(
                    hex_id=hex_id,
                    hub_id=hub_id,
                    path_index=len(paths),
                    stops=stops,
                    duration_minutes=duration,
                    transfers=transfers,
                    score=score,
                )
            )
        paths.sort(key=lambda item: item.score, reverse=True)
        return paths[: self._config.max_paths]

    @staticmethod
    def _extract_stops(legs: Iterable[dict[str, object]]) -> list[str]:
        stops: list[str] = []
        for leg in legs:
            name = leg.get("from")
            if isinstance(name, dict):
                name = name.get("name")
            if name:
                stops.append(str(name))
        if legs:
            last = legs[-1].get("to")
            if isinstance(last, dict):
                last = last.get("name")
            if last:
                stops.append(str(last))
        return stops

    def _store_cache(self, key: tuple[str, str], value: list[TransitPath]) -> None:
        self._cache[key] = value
        self._cache.move_to_end(key)
        cache_size = max(self._config.cache_size, 1)
        while len(self._cache) > cache_size:
            self._cache.popitem(last=False)


class StopBufferBuilder:
    """Buffer stops and collect nearby POIs using spatial indexing."""

    def __init__(
        self,
        buffer_m: float,
        categories: Sequence[str],
        walk_speed_m_per_min: float = WALKING_SPEED_M_PER_MIN,
    ) -> None:
        self._buffer_m = buffer_m
        self._categories = set(categories)
        self._walk_speed = walk_speed_m_per_min
        self._to_m = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)

    def collect(
        self,
        paths: Sequence[TransitPath],
        stops: pd.DataFrame,
        pois: pd.DataFrame,
    ) -> pd.DataFrame:
        if not paths:
            return pd.DataFrame(
                columns=
                [
                    "hex_id",
                    "hub_id",
                    "path_index",
                    "stop_id",
                    "stop_name",
                    "poi_id",
                    "category",
                    "quality",
                    "distance_m",
                    "walk_minutes",
                ]
            )
        stops = stops.copy()
        if "stop_id" not in stops.columns and "stop_name" not in stops.columns:
            raise KeyError("stops dataframe must include stop_id or stop_name column")
        if "lon" not in stops.columns or "lat" not in stops.columns:
            raise KeyError("stops dataframe must include lon and lat columns")
        stops["geometry"] = stops.apply(lambda row: Point(float(row["lon"]), float(row["lat"])), axis=1)
        poi_frame = pois.copy()
        if "category" not in poi_frame.columns:
            raise KeyError("pois dataframe must include category column")
        if "poi_id" not in poi_frame.columns:
            raise KeyError("pois dataframe must include poi_id column")
        if "lon" not in poi_frame.columns or "lat" not in poi_frame.columns:
            raise KeyError("pois dataframe must include lon and lat columns")
        poi_frame = poi_frame[poi_frame["category"].isin(self._categories)].copy()
        if poi_frame.empty:
            return pd.DataFrame(
                columns=
                [
                    "hex_id",
                    "hub_id",
                    "path_index",
                    "stop_id",
                    "stop_name",
                    "poi_id",
                    "category",
                    "quality",
                    "distance_m",
                    "walk_minutes",
                ]
            )
        poi_frame["geometry"] = poi_frame.apply(lambda row: Point(float(row["lon"]), float(row["lat"])), axis=1)
        poi_frame["quality"] = poi_frame.get("quality", pd.Series(50.0, index=poi_frame.index)).fillna(50.0)

        def transform_to_m(geom):
            return transform(self._to_m.transform, geom)
        stops["geometry_m"] = stops["geometry"].apply(transform_to_m)
        poi_frame["geometry_m"] = poi_frame["geometry"].apply(transform_to_m)

        index = Index()
        for idx, geom in enumerate(poi_frame["geometry_m"]):
            index.insert(idx, geom.bounds)

        records: list[dict[str, object]] = []
        stop_lookup = self._build_stop_lookup(stops)
        for path in paths:
            for _position, stop_name in enumerate(path.stops):
                stop_record = stop_lookup.get(stop_name)
                if stop_record is None:
                    continue
                stop_geom = stop_record["geometry_m"]
                buffer_geom = stop_geom.buffer(self._buffer_m)
                for poi_idx in index.intersection(buffer_geom.bounds):
                    poi = poi_frame.iloc[poi_idx]
                    poi_geom = poi["geometry_m"]
                    if not buffer_geom.contains(poi_geom):
                        continue
                    distance = float(stop_geom.distance(poi_geom))
                    walk_minutes = distance / self._walk_speed if self._walk_speed > 0 else 0.0
                    records.append(
                        {
                            "hex_id": path.hex_id,
                            "hub_id": path.hub_id,
                            "path_index": path.path_index,
                            "stop_id": stop_record["stop_id"],
                            "stop_name": stop_record["stop_name"],
                            "poi_id": poi["poi_id"],
                            "category": poi["category"],
                            "quality": float(poi["quality"]),
                            "distance_m": distance,
                            "walk_minutes": walk_minutes,
                        }
                    )
        if not records:
            return pd.DataFrame(
                columns=
                [
                    "hex_id",
                    "hub_id",
                    "path_index",
                    "stop_id",
                    "stop_name",
                    "poi_id",
                    "category",
                    "quality",
                    "distance_m",
                    "walk_minutes",
                ]
            )
        mapping = pd.DataFrame.from_records(records)
        mapping.sort_values("distance_m", inplace=True)
        dedup_columns = ["hex_id", "hub_id", "path_index", "poi_id"]
        mapping = mapping.drop_duplicates(subset=dedup_columns, keep="first")
        return mapping.reset_index(drop=True)

    @staticmethod
    def _build_stop_lookup(stops: pd.DataFrame) -> dict[str, dict[str, object]]:
        lookup: dict[str, dict[str, object]] = {}
        for _, row in stops.iterrows():
            stop_id = str(row.get("stop_id") or row.get("stop_name"))
            stop_name = str(row.get("stop_name") or row.get("stop_id"))
            lookup[stop_id] = {
                "stop_id": stop_id,
                "stop_name": stop_name,
                "geometry_m": row["geometry_m"],
            }
            lookup[stop_name] = lookup[stop_id]
        return lookup


class ErrandChainScorer:
    """Compute errand chain opportunities along transit paths."""

    def __init__(self, config: CorridorParams) -> None:
        self._config = config

    def score(self, mapping: pd.DataFrame) -> pd.DataFrame:
        required = {
            "hex_id",
            "hub_id",
            "path_index",
            "stop_id",
            "category",
            "quality",
            "walk_minutes",
        }
        missing = required - set(mapping.columns)
        if missing:
            raise KeyError(f"mapping dataframe missing columns: {sorted(missing)}")
        records: list[dict[str, object]] = []
        for (hex_id, hub_id, path_index), group in mapping.groupby(["hex_id", "hub_id", "path_index"]):
            for pair in self._config.pair_categories:
                cat_a, cat_b = pair
                subset_a = group[group["category"] == cat_a]
                subset_b = group[group["category"] == cat_b]
                if subset_a.empty or subset_b.empty:
                    continue
                for _, poi_a in subset_a.iterrows():
                    for _, poi_b in subset_b.iterrows():
                        if poi_a["stop_id"] == poi_b["stop_id"]:
                            continue
                        detour = float(poi_a["walk_minutes"]) + float(poi_b["walk_minutes"])
                        quality = self._adjust_quality(poi_a) + self._adjust_quality(poi_b)
                        key = f"{cat_a}+{cat_b}"
                        weight = self._config.chain_weights.get(key, 1.0)
                        records.append(
                            {
                                "hex_id": hex_id,
                                "hub_id": hub_id,
                                "path_index": path_index,
                                "quality": quality,
                                "likelihood": weight,
                                "detour_minutes": detour,
                                "category_pair": key,
                            }
                        )
        chains = pd.DataFrame.from_records(records)
        if chains.empty:
            return chains
        valid = chains[chains["detour_minutes"] <= self._config.detour_cap_min].copy()
        return valid.reset_index(drop=True)

    def _adjust_quality(self, poi: pd.Series) -> float:
        quality = float(poi.get("quality", 0.0))
        walk = float(poi.get("walk_minutes", 0.0))
        return quality * np.exp(-self._config.walk_decay_alpha * walk)


__all__ = [
    "ErrandChainScorer",
    "StopBufferBuilder",
    "TransitPath",
    "TransitPathIdentifier",
]
