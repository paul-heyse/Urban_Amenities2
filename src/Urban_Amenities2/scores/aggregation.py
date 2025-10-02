from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import pandas as pd


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


__all__ = ["aggregate_scores", "WeightConfig"]
