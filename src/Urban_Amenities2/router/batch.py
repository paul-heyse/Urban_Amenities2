from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import pandas as pd  # type: ignore[import-untyped]
from diskcache import Cache  # type: ignore[import-untyped]

from ..logging_utils import get_logger
from .api import RoutingAPI

LOGGER = get_logger("aucs.router.batch")


@dataclass
class BatchConfig:
    cache_dir: Path = Path("data/cache/skims")
    mode: str = "car"
    period: str | None = None


class SkimBuilder:
    def __init__(self, api: RoutingAPI, config: BatchConfig):
        self.api = api
        self.config = config
        self.cache = Cache(str(config.cache_dir))

    def _cache_key(self, origins: Sequence[tuple[float, float]], destinations: Sequence[tuple[float, float]]) -> str:
        payload = json.dumps({"origins": origins, "destinations": destinations, "mode": self.config.mode, "period": self.config.period})
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def matrix(
        self,
        origins: Sequence[tuple[float, float]],
        destinations: Sequence[tuple[float, float]],
    ) -> pd.DataFrame:
        key = self._cache_key(origins, destinations)
        if key in self.cache:
            LOGGER.info("skim_cache_hit", key=key)
            return pd.DataFrame(self.cache[key])
        LOGGER.info("skim_cache_miss", key=key)
        frame = self.api.matrix(self.config.mode, origins, destinations, period=self.config.period)
        self.cache[key] = frame.to_dict("records")
        return frame

    def hex_to_poi(
        self,
        hex_coords: dict[str, tuple[float, float]],
        poi_coords: dict[str, tuple[float, float]],
    ) -> pd.DataFrame:
        origins = list(hex_coords.values())
        destinations = list(poi_coords.values())
        frame = self.matrix(origins, destinations)
        hex_list = list(hex_coords.keys())
        poi_list = list(poi_coords.keys())
        frame["origin_hex"] = frame["origin_index"].map(lambda idx: hex_list[idx])
        frame["poi_id"] = frame["destination_index"].map(lambda idx: poi_list[idx])
        return frame

    def write_parquet(self, frame: pd.DataFrame, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(path)
        LOGGER.info("skim_written", path=str(path), rows=len(frame))


__all__ = ["SkimBuilder", "BatchConfig"]
