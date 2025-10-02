from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping

import numpy as np
import pandas as pd

from ..logging_utils import get_logger

LOGGER = get_logger("aucs.scores.sou")

MONTH_NAMES = (
    "jan",
    "feb",
    "mar",
    "apr",
    "may",
    "jun",
    "jul",
    "aug",
    "sep",
    "oct",
    "nov",
    "dec",
)


@dataclass(slots=True)
class ClimateComfortConfig:
    comfortable_temperature: tuple[float, float] = (50.0, 80.0)
    precipitation_threshold: float = 0.5
    wind_threshold: float = 15.0
    month_weights: Mapping[str, float] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.month_weights is None:
            self.month_weights = {
                "mar": 1.0,
                "apr": 1.1,
                "may": 1.2,
                "jun": 1.3,
                "jul": 1.3,
                "aug": 1.2,
                "sep": 1.1,
                "oct": 1.0,
                "nov": 0.6,
                "dec": 0.4,
                "jan": 0.4,
                "feb": 0.5,
            }
        if len(self.comfortable_temperature) != 2:
            raise ValueError("comfortable_temperature must contain (min, max)")
        lo, hi = self.comfortable_temperature
        if hi <= lo:
            raise ValueError("temperature max must exceed min")
        if self.precipitation_threshold <= 0:
            raise ValueError("precipitation_threshold must be positive")
        if self.wind_threshold <= 0:
            raise ValueError("wind_threshold must be positive")


@dataclass(slots=True)
class SeasonalOutdoorsConfig:
    climate: ClimateComfortConfig = field(default_factory=ClimateComfortConfig)
    parks_column: str = "parks_score"
    output_column: str = "SOU"


def _column_name(prefix: str, month: str) -> str:
    return f"{prefix}_{month.lower()}"


def _temperature_comfort(temperature: float, config: ClimateComfortConfig) -> float:
    lo, hi = config.comfortable_temperature
    if lo <= temperature <= hi:
        return 1.0
    if temperature < lo:
        delta = lo - temperature
        return float(np.clip(1.0 - delta / 20.0, 0.0, 1.0))
    delta = temperature - hi
    return float(np.clip(1.0 - delta / 20.0, 0.0, 1.0))


def _precipitation_comfort(precip: float, config: ClimateComfortConfig) -> float:
    if precip <= config.precipitation_threshold:
        return 1.0
    delta = precip - config.precipitation_threshold
    return float(np.clip(1.0 - delta / config.precipitation_threshold, 0.0, 1.0))


def _wind_comfort(wind: float, config: ClimateComfortConfig) -> float:
    if wind <= config.wind_threshold:
        return 1.0
    delta = wind - config.wind_threshold
    return float(np.clip(1.0 - delta / config.wind_threshold, 0.0, 1.0))


def compute_monthly_comfort(
    *,
    temperature: float,
    precipitation: float,
    wind: float,
    config: ClimateComfortConfig,
) -> float:
    temp = _temperature_comfort(temperature, config)
    precip = _precipitation_comfort(precipitation, config)
    wind_score = _wind_comfort(wind, config)
    return float(np.clip(temp * precip * wind_score, 0.0, 1.0))


def compute_sigma_out(row: pd.Series, config: ClimateComfortConfig) -> float:
    weights = []
    scores = []
    for month, weight in config.month_weights.items():
        temp = row.get(_column_name("temp", month))
        precip = row.get(_column_name("precip", month))
        wind = row.get(_column_name("wind", month))
        if pd.isna(temp) or pd.isna(precip) or pd.isna(wind):
            continue
        comfort = compute_monthly_comfort(
            temperature=float(temp),
            precipitation=float(precip),
            wind=float(wind),
            config=config,
        )
        weights.append(weight)
        scores.append(comfort)
    if not scores:
        return 0.0
    weighted = float(np.average(scores, weights=weights))
    return float(np.clip(weighted, 0.0, 1.0))


class SeasonalOutdoorsCalculator:
    def __init__(self, config: SeasonalOutdoorsConfig | None = None):
        self.config = config or SeasonalOutdoorsConfig()

    def compute(
        self,
        parks: pd.DataFrame,
        climate: pd.DataFrame,
        *,
        id_column: str = "hex_id",
    ) -> pd.DataFrame:
        required_columns = {id_column, self.config.parks_column}
        missing = required_columns - set(parks.columns)
        if missing:
            raise KeyError(f"parks dataframe missing columns: {sorted(missing)}")
        joined = parks.merge(climate, on=id_column, how="left", suffixes=(None, "_climate"))
        LOGGER.info("sou_join", rows=len(joined))
        sigma_values = joined.apply(lambda row: compute_sigma_out(row, self.config.climate), axis=1)
        joined["sigma_out"] = sigma_values
        joined[self.config.output_column] = (
            joined[self.config.parks_column].fillna(0.0) * joined["sigma_out"]
        )
        joined[self.config.output_column] = joined[self.config.output_column].clip(0.0, 100.0)
        joined.loc[joined[self.config.parks_column] <= 0, self.config.output_column] = 0.0
        return joined[[id_column, self.config.output_column, "sigma_out"]]


def ensure_monthly_columns(frame: pd.DataFrame, prefixes: Iterable[str]) -> None:
    missing: list[str] = []
    for prefix in prefixes:
        for month in MONTH_NAMES:
            column = _column_name(prefix, month)
            if column not in frame.columns:
                missing.append(column)
    if missing:
        raise KeyError(f"climate dataframe missing monthly columns: {missing}")


__all__ = [
    "ClimateComfortConfig",
    "SeasonalOutdoorsConfig",
    "SeasonalOutdoorsCalculator",
    "compute_monthly_comfort",
    "compute_sigma_out",
    "ensure_monthly_columns",
]
