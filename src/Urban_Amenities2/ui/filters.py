"""Advanced filtering capabilities for the AUCS UI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass
class FilterConfig:
    """Configuration for data filters."""

    state: list[str] | None = None
    metro: list[str] | None = None
    score_min: float | None = None
    score_max: float | None = None
    population_density_min: float | None = None
    population_density_max: float | None = None
    land_use: list[str] | None = None


def apply_filters(df: pd.DataFrame, config: FilterConfig) -> pd.DataFrame:
    """
    Apply filters to the dataset.

    Args:
        df: DataFrame with hex-level scores
        config: Filter configuration

    Returns:
        Filtered DataFrame
    """
    filtered = df.copy()

    if config.state is not None:
        filtered = filtered[filtered["state"].isin(config.state)]

    if config.metro is not None:
        filtered = filtered[filtered["metro"].isin(config.metro)]

    if config.score_min is not None:
        filtered = filtered[filtered["aucs"] >= config.score_min]

    if config.score_max is not None:
        filtered = filtered[filtered["aucs"] <= config.score_max]

    if config.population_density_min is not None:
        filtered = filtered[filtered["pop_density"] >= config.population_density_min]

    if config.population_density_max is not None:
        filtered = filtered[filtered["pop_density"] <= config.population_density_max]

    if config.land_use is not None:
        filtered = filtered[filtered["land_use"].isin(config.land_use)]

    return filtered


def get_filter_options(df: pd.DataFrame) -> dict[str, Any]:
    """
    Extract available filter options from the dataset.

    Args:
        df: DataFrame with hex-level scores

    Returns:
        Dictionary with available filter values
    """
    return {
        "states": sorted(df["state"].unique().tolist()),
        "metros": sorted(df["metro"].unique().tolist()),
        "score_range": [float(df["aucs"].min()), float(df["aucs"].max())],
        "land_uses": sorted(df["land_use"].unique().tolist()) if "land_use" in df.columns else [],
        "population_density_range": (
            [float(df["pop_density"].min()), float(df["pop_density"].max())]
            if "pop_density" in df.columns
            else [0, 0]
        ),
    }

