from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

import numpy as np
import pandas as pd

from ..logging_utils import get_logger

LOGGER = get_logger("aucs.scores.muhaa")


def _minmax(series: pd.Series) -> pd.Series:
    if series.empty:
        return series
    lo = series.min()
    hi = series.max()
    if np.isclose(hi, lo):
        return pd.Series(np.full(len(series), 100.0), index=series.index)
    scaled = (series - lo) / (hi - lo)
    return scaled * 100.0


@dataclass(slots=True)
class HubMassWeights:
    population: float = 0.4
    gdp: float = 0.3
    poi: float = 0.2
    culture: float = 0.1

    def normalised(self) -> Mapping[str, float]:
        weights = {
            "population": self.population,
            "gdp": self.gdp,
            "poi": self.poi,
            "culture": self.culture,
        }
        total = sum(weights.values())
        if total <= 0:
            raise ValueError("hub mass weights must sum to positive value")
        return {key: value / total for key, value in weights.items()}


@dataclass(slots=True)
class AccessibilityConfig:
    alpha: float = 0.03
    travel_time_column: str = "travel_minutes"
    id_column: str = "hex_id"
    destination_column: str = "destination_id"
    impedance_column: str | None = None


@dataclass(slots=True)
class MuhAAConfig:
    hub_weights: HubMassWeights = field(default_factory=HubMassWeights)
    hub_alpha: float = 0.03
    airport_alpha: float = 0.025
    hub_contribution: float = 0.7
    airport_contribution: float = 0.3
    output_column: str = "MUHAA"

    def __post_init__(self) -> None:
        if not (0 <= self.hub_contribution <= 1 and 0 <= self.airport_contribution <= 1):
            raise ValueError("contributions must be between 0 and 1")
        total = self.hub_contribution + self.airport_contribution
        if total == 0:
            raise ValueError("at least one contribution must be positive")
        self.hub_contribution /= total
        self.airport_contribution /= total


def compute_hub_mass(hubs: pd.DataFrame, weights: HubMassWeights) -> pd.DataFrame:
    required = {"hub_id", "population", "gdp", "poi", "culture"}
    missing = required - set(hubs.columns)
    if missing:
        raise KeyError(f"hubs dataframe missing columns: {sorted(missing)}")
    hubs = hubs.copy()
    for column in ("population", "gdp", "poi", "culture"):
        hubs[f"{column}_scaled"] = _minmax(hubs[column].astype(float))
    weights_norm = weights.normalised()
    hubs["mass"] = sum(hubs[f"{column}_scaled"] * weight for column, weight in weights_norm.items())
    LOGGER.info("hub_mass", hubs=len(hubs))
    return hubs[["hub_id", "mass"]]


def _generalised_cost(row: pd.Series, config: AccessibilityConfig) -> float:
    travel = float(row[config.travel_time_column])
    if config.impedance_column and config.impedance_column in row:
        travel += float(row[config.impedance_column])
    return travel


def compute_accessibility(
    travel: pd.DataFrame,
    masses: pd.DataFrame,
    *,
    config: AccessibilityConfig,
    alpha: float,
) -> pd.DataFrame:
    merged = travel.merge(masses, left_on=config.destination_column, right_on="hub_id", how="left")
    merged = merged.dropna(subset=["mass"])
    if merged.empty:
        return pd.DataFrame({config.id_column: [], "accessibility": []})
    merged["gtc"] = merged.apply(lambda row: _generalised_cost(row, config), axis=1)
    merged["contribution"] = merged["mass"] * np.exp(-alpha * merged["gtc"])
    aggregated = merged.groupby(config.id_column)["contribution"].sum().reset_index()
    aggregated.rename(columns={"contribution": "accessibility"}, inplace=True)
    aggregated["accessibility"] = _minmax(aggregated["accessibility"])
    return aggregated


def compute_airport_accessibility(
    travel: pd.DataFrame,
    airports: pd.DataFrame,
    *,
    config: AccessibilityConfig,
    alpha: float,
) -> pd.DataFrame:
    required = {"airport_id", "enplanements"}
    missing = required - set(airports.columns)
    if missing:
        raise KeyError(f"airports dataframe missing columns: {sorted(missing)}")
    airports = airports.copy()
    airports["mass"] = _minmax(airports["enplanements"].astype(float))
    airports.rename(columns={"airport_id": "hub_id"}, inplace=True)
    return compute_accessibility(travel, airports[["hub_id", "mass"]], config=config, alpha=alpha)


class MuhAAScore:
    def __init__(self, config: MuhAAConfig | None = None):
        self.config = config or MuhAAConfig()

    def compute(
        self,
        hubs: pd.DataFrame,
        hub_travel: pd.DataFrame,
        airports: pd.DataFrame,
        airport_travel: pd.DataFrame,
        *,
        id_column: str = "hex_id",
    ) -> pd.DataFrame:
        hub_masses = compute_hub_mass(hubs, self.config.hub_weights)
        hub_access = compute_accessibility(
            hub_travel,
            hub_masses,
            config=AccessibilityConfig(id_column=id_column),
            alpha=self.config.hub_alpha,
        )
        airport_access = compute_airport_accessibility(
            airport_travel,
            airports,
            config=AccessibilityConfig(id_column=id_column),
            alpha=self.config.airport_alpha,
        )
        combined = pd.merge(hub_access, airport_access, on=id_column, how="outer", suffixes=("_hub", "_airport"))
        combined[["accessibility_hub", "accessibility_airport"]] = combined[[
            "accessibility_hub",
            "accessibility_airport",
        ]].fillna(0.0)
        combined[self.config.output_column] = (
            combined["accessibility_hub"] * self.config.hub_contribution
            + combined["accessibility_airport"] * self.config.airport_contribution
        )
        combined[self.config.output_column] = combined[self.config.output_column].clip(0.0, 100.0)
        return combined[[id_column, self.config.output_column, "accessibility_hub", "accessibility_airport"]]


__all__ = [
    "HubMassWeights",
    "AccessibilityConfig",
    "MuhAAConfig",
    "compute_hub_mass",
    "compute_accessibility",
    "compute_airport_accessibility",
    "MuhAAScore",
]
