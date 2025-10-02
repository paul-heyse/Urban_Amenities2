from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import pandas as pd

from ..config.params import AUCSParams


@dataclass
class WeightConfig:
    weights: Dict[str, float]

    def normalised(self) -> Dict[str, float]:
        total = sum(self.weights.values())
        if total == 0:
            raise ValueError("Weights must sum to a positive value")
        return {key: value / total for key, value in self.weights.items()}


def aggregate_scores(frame: pd.DataFrame, value_column: str, weight_config: WeightConfig) -> pd.DataFrame:
    weights = weight_config.normalised()
    for subscore, weight in weights.items():
        if subscore not in frame.columns:
            raise ValueError(f"Subscore {subscore} missing from frame")
    def _aggregate(row: pd.Series) -> float:
        total = 0.0
        for subscore, weight in weights.items():
            total += row[subscore] * weight
        return total
    frame = frame.copy()
    frame[value_column] = frame.apply(_aggregate, axis=1)
    return frame


def build_weight_config(params: AUCSParams) -> WeightConfig:
    """Create a :class:`WeightConfig` from AUCS parameters."""

    return WeightConfig(params.subscores.model_dump())


def compute_total_aucs(
    subscores: pd.DataFrame,
    params: AUCSParams,
    *,
    id_column: str = "hex_id",
    output_column: str = "aucs",
) -> pd.DataFrame:
    """Aggregate AUCS subscores using weights from the parameter configuration."""

    if id_column not in subscores.columns:
        raise KeyError(f"subscores dataframe missing id column '{id_column}'")
    config = build_weight_config(params)
    frame = subscores.copy()
    aggregated = aggregate_scores(frame, output_column, config)
    return aggregated[[id_column, output_column]]


__all__ = ["WeightConfig", "aggregate_scores", "build_weight_config", "compute_total_aucs"]
