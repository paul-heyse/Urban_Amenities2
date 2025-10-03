from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ..logging_utils import get_logger
from ..math.satiation import apply_satiation
from ..monitoring.metrics import METRICS, track_operation

LOGGER = get_logger("aucs.scores.parks")


@dataclass(slots=True)
class ParkQualityWeights:
    area: float = 0.4
    amenities: float = 0.35
    designation: float = 0.25

    def normalised(self) -> tuple[float, float, float]:
        total = self.area + self.amenities + self.designation
        if total <= 0:
            raise ValueError("Quality weights must sum to positive value")
        return (self.area / total, self.amenities / total, self.designation / total)


@dataclass(slots=True)
class ParkQualityConfig:
    area_column: str = "area_acres"
    amenities_column: str = "amenities"
    designation_column: str = "designation"
    quality_column: str = "quality"
    area_range: tuple[float, float] = (2.0, 500.0)
    amenities_range: tuple[float, float] = (0.0, 20.0)
    designation_weights: Mapping[str, float] = field(
        default_factory=lambda: {
            "national_park": 1.0,
            "state_park": 0.9,
            "regional_park": 0.8,
            "city_park": 0.7,
            "open_space": 0.6,
            "trailhead": 0.5,
        }
    )
    default_designation_weight: float = 0.5
    weights: ParkQualityWeights = field(default_factory=ParkQualityWeights)

    def _scale(self, value: float, bounds: tuple[float, float]) -> float:
        lo, hi = bounds
        if hi <= lo:
            raise ValueError("Upper bound must exceed lower bound")
        clipped = np.clip(value, lo, hi)
        if hi <= 0:
            return 0.0
        return float((np.log1p(clipped) - np.log1p(lo)) / (np.log1p(hi) - np.log1p(lo)))

    def designation_score(self, raw: str | None) -> float:
        if raw is None:
            return self.default_designation_weight
        key = str(raw).strip().lower()
        return float(
            np.clip(self.designation_weights.get(key, self.default_designation_weight), 0.0, 1.0)
        )

    def compute(self, row: pd.Series) -> float:
        if self.quality_column in row and pd.notna(row[self.quality_column]):
            return float(np.clip(row[self.quality_column], 0.0, 100.0))
        area_score = self._scale(float(row.get(self.area_column, 0.0) or 0.0), self.area_range)
        amenity_score = self._scale(
            float(row.get(self.amenities_column, 0.0) or 0.0), self.amenities_range
        )
        designation_score = self.designation_score(row.get(self.designation_column))
        w_area, w_amenity, w_designation = self.weights.normalised()
        blended = (
            w_area * area_score + w_amenity * amenity_score + w_designation * designation_score
        )
        return float(np.clip(blended * 100.0, 0.0, 100.0))


@dataclass(slots=True)
class ParksTrailsAccessConfig:
    poi_id_column: str = "poi_id"
    id_column: str = "hex_id"
    weight_column: str = "weight"
    ces_rho: float = 0.5
    exposure_scale: float = 8.0
    satiation_kappa: float = 0.35
    quality: ParkQualityConfig = field(default_factory=ParkQualityConfig)


def _ces_aggregate(values: np.ndarray, weights: np.ndarray, rho: float) -> float:
    if weights.sum() == 0:
        return 0.0
    weights = weights / weights.sum()
    if np.all(values == 0):
        return 0.0
    if abs(rho) < 1e-6:
        return float(np.exp(np.sum(weights * np.log(np.clip(values, 1e-12, 1.0)))))
    if abs(rho - 1.0) < 1e-6:
        return float(np.sum(weights * values))
    return float(np.power(np.sum(weights * np.power(values, rho)), 1.0 / rho))


class ParksTrailsAccessCalculator:
    def __init__(self, config: ParksTrailsAccessConfig | None = None) -> None:
        self.config = config or ParksTrailsAccessConfig()

    def _quality_table(self, parks: pd.DataFrame) -> pd.DataFrame:
        if self.config.poi_id_column not in parks.columns:
            raise KeyError(f"parks dataframe missing '{self.config.poi_id_column}' column")
        frame = parks.copy()
        quality_scores = frame.apply(self.config.quality.compute, axis=1)
        table = frame[[self.config.poi_id_column]].copy()
        table["quality_score"] = quality_scores
        return table

    def compute(
        self, parks: pd.DataFrame, accessibility: pd.DataFrame, *, id_column: str | None = None
    ) -> pd.DataFrame:
        id_column = id_column or self.config.id_column
        table = self._quality_table(parks)
        if table.empty:
            return pd.DataFrame({id_column: [], "parks_score": []})
        if self.config.poi_id_column not in accessibility.columns:
            raise KeyError(f"accessibility missing '{self.config.poi_id_column}' column")
        frame = accessibility.copy()
        if id_column not in frame.columns and "origin_hex" in frame.columns:
            frame = frame.rename(columns={"origin_hex": id_column})
        if id_column not in frame.columns:
            raise KeyError(f"accessibility missing '{id_column}' column")
        if self.config.weight_column not in frame.columns:
            raise KeyError(f"accessibility missing '{self.config.weight_column}' column")
        merged = frame.merge(table, on=self.config.poi_id_column, how="inner")
        if merged.empty:
            return pd.DataFrame({id_column: [], "parks_score": []})
        merged[self.config.weight_column] = (
            merged[self.config.weight_column].astype(float).clip(lower=0.0)
        )
        LOGGER.info(
            "parks_access_merge",
            rows=len(merged),
            unique_hexes=merged[id_column].nunique(),
            unique_parks=table[self.config.poi_id_column].nunique(),
        )
        with track_operation(
            "parks_accessibility", metrics=METRICS, logger=LOGGER, items=len(merged)
        ):
            grouped = merged.groupby(id_column, dropna=False)
            scores: list[dict[str, float]] = []
            for hex_id, group in grouped:
                weights = group[self.config.weight_column].to_numpy(dtype=float)
                if weights.sum() == 0:
                    scores.append({id_column: hex_id, "parks_score": 0.0})
                    continue
                values = group["quality_score"].to_numpy(dtype=float) / 100.0
                ces_value = _ces_aggregate(values, weights, self.config.ces_rho)
                exposure = max(ces_value, 0.0) * self.config.exposure_scale
                saturated = apply_satiation(np.asarray([exposure]), self.config.satiation_kappa)[0]
                scores.append(
                    {id_column: hex_id, "parks_score": float(np.clip(saturated, 0.0, 100.0))}
                )
        result = pd.DataFrame(scores)
        return result


__all__ = [
    "ParkQualityConfig",
    "ParkQualityWeights",
    "ParksTrailsAccessCalculator",
    "ParksTrailsAccessConfig",
]
