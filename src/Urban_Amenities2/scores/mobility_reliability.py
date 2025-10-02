from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

import numpy as np
import pandas as pd


HEX_ID = "hex_id"


def _ensure_column(frame: pd.DataFrame, column: str) -> None:
    if column not in frame.columns:
        raise KeyError(f"expected column '{column}' in dataframe")


def compute_frequent_transit_exposure(
    stops: pd.DataFrame,
    *,
    headway_column: str = "headway_peak",
    distance_column: str = "distance_m",
    threshold_minutes: float = 15.0,
    radius_meters: float = 500.0,
    output_column: str = "C1",
) -> pd.DataFrame:
    for column in (HEX_ID, headway_column, distance_column):
        _ensure_column(stops, column)
    nearby = stops[stops[distance_column] <= radius_meters]
    if nearby.empty:
        return pd.DataFrame({HEX_ID: [], output_column: []})
    nearby = nearby.copy()
    nearby["frequent"] = nearby[headway_column] <= threshold_minutes
    summary = nearby.groupby(HEX_ID)["frequent"].mean().reset_index()
    summary[output_column] = (summary["frequent"] * 100.0).clip(0.0, 100.0)
    return summary[[HEX_ID, output_column]]


def compute_service_span(
    services: pd.DataFrame,
    *,
    service_hours_column: str = "service_hours",
    early_column: str = "has_early",
    late_column: str = "has_late",
    weekend_column: str = "has_weekend",
    output_column: str = "C2",
) -> pd.DataFrame:
    for column in (HEX_ID, service_hours_column, early_column, late_column, weekend_column):
        _ensure_column(services, column)
    services = services.copy()
    services["hours_score"] = (services[service_hours_column] / 24.0).clip(0.0, 1.0)
    services["coverage_score"] = (
        services[[early_column, late_column, weekend_column]].sum(axis=1) / 3.0
    )
    services[output_column] = (services[["hours_score", "coverage_score"]].mean(axis=1) * 100.0).clip(
        0.0, 100.0
    )
    summary = services.groupby(HEX_ID)[output_column].max().reset_index()
    return summary


def compute_on_time_reliability(
    reliability: pd.DataFrame,
    *,
    on_time_column: str = "on_time_pct",
    frequency_column: str = "frequency_weight",
    output_column: str = "C3",
) -> pd.DataFrame:
    for column in (HEX_ID, on_time_column, frequency_column):
        _ensure_column(reliability, column)
    reliability = reliability.copy()
    reliability["weight"] = reliability[frequency_column].clip(lower=0.0)
    grouped = reliability.groupby(HEX_ID)
    weighted = grouped.apply(
        lambda df: 0.0
        if df["weight"].sum() == 0
        else float(np.average(df[on_time_column].clip(0.0, 100.0), weights=df["weight"]))
    )
    return weighted.reset_index().rename(columns={0: output_column})


def compute_network_redundancy(
    redundancy: pd.DataFrame,
    *,
    transit_routes_column: str = "transit_routes",
    road_routes_column: str = "road_routes",
    output_column: str = "C4",
) -> pd.DataFrame:
    for column in (HEX_ID, transit_routes_column, road_routes_column):
        _ensure_column(redundancy, column)
    redundancy = redundancy.copy()
    redundancy["route_total"] = redundancy[transit_routes_column].clip(lower=0) + redundancy[
        road_routes_column
    ].clip(lower=0)
    redundancy[output_column] = (1.0 - 1.0 / (1.0 + redundancy["route_total"])) * 100.0
    summary = redundancy.groupby(HEX_ID)[output_column].max().reset_index()
    summary[output_column] = summary[output_column].clip(0.0, 100.0)
    return summary


def compute_micromobility_presence(
    micro: pd.DataFrame,
    *,
    station_column: str = "stations",
    area_column: str = "area_sqkm",
    output_column: str = "C5",
) -> pd.DataFrame:
    for column in (HEX_ID, station_column, area_column):
        _ensure_column(micro, column)
    micro = micro.copy()
    micro["density"] = micro[station_column] / micro[area_column].replace(0, np.nan)
    micro["density"] = micro["density"].fillna(0.0)
    grouped = micro.groupby(HEX_ID)["density"].mean().reset_index()
    if grouped.empty:
        grouped[output_column] = []  # pragma: no cover
        return grouped[[HEX_ID, output_column]]
    max_density = grouped["density"].max()
    if max_density <= 0:
        grouped[output_column] = 0.0
    else:
        grouped[output_column] = grouped["density"] / max_density * 100.0
    grouped[output_column] = grouped[output_column].clip(0.0, 100.0)
    return grouped[[HEX_ID, output_column]]


@dataclass(slots=True)
class MorrWeights:
    frequent: float = 1.0
    span: float = 1.0
    reliability: float = 1.0
    redundancy: float = 1.0
    micromobility: float = 1.0

    def as_dict(self) -> Mapping[str, float]:
        weights = {
            "C1": self.frequent,
            "C2": self.span,
            "C3": self.reliability,
            "C4": self.redundancy,
            "C5": self.micromobility,
        }
        total = sum(weights.values())
        if total <= 0:
            raise ValueError("MORR weights must sum to positive value")
        return {key: value / total for key, value in weights.items()}


@dataclass(slots=True)
class MorrConfig:
    weights: MorrWeights = field(default_factory=MorrWeights)
    output_column: str = "MORR"


class MobilityReliabilityCalculator:
    def __init__(self, config: MorrConfig | None = None):
        self.config = config or MorrConfig()

    def aggregate(self, components: pd.DataFrame) -> pd.DataFrame:
        weights = self.config.weights.as_dict()
        for component in weights:
            if component not in components.columns:
                raise KeyError(f"component {component} missing from dataframe")
        scores = components.copy()
        scores[self.config.output_column] = (
            sum(scores[component] * weight for component, weight in weights.items())
        ).clip(0.0, 100.0)
        return scores[[HEX_ID, self.config.output_column]]

    def compute(
        self,
        c1: pd.DataFrame,
        c2: pd.DataFrame,
        c3: pd.DataFrame,
        c4: pd.DataFrame,
        c5: pd.DataFrame,
    ) -> pd.DataFrame:
        components = (
            c1.merge(c2, on=HEX_ID, how="outer")
            .merge(c3, on=HEX_ID, how="outer")
            .merge(c4, on=HEX_ID, how="outer")
            .merge(c5, on=HEX_ID, how="outer")
            .fillna(0.0)
        )
        return self.aggregate(components)


__all__ = [
    "compute_frequent_transit_exposure",
    "compute_service_span",
    "compute_on_time_reliability",
    "compute_network_redundancy",
    "compute_micromobility_presence",
    "MorrWeights",
    "MorrConfig",
    "MobilityReliabilityCalculator",
]
