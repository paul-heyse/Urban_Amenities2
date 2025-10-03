from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd


@dataclass
class NormalizationConfig:
    mode: Literal["percentile", "standard"] = "percentile"
    lower_percentile: float = 5.0
    upper_percentile: float = 95.0
    standard_target: float | None = None


def percentile_normalize(frame: pd.DataFrame, group: str, value: str, config: NormalizationConfig) -> pd.DataFrame:
    records = []
    for _key, subset in frame.groupby(group):
        low = np.percentile(subset[value], config.lower_percentile)
        high = np.percentile(subset[value], config.upper_percentile)
        if high == low:
            normalized = np.zeros(len(subset))
        else:
            normalized = np.clip((subset[value] - low) / (high - low), 0, 1) * 100
        result = subset.copy()
        result[f"{value}_normalized"] = normalized
        records.append(result)
    return pd.concat(records, ignore_index=True)


def standard_normalize(frame: pd.DataFrame, value: str, target: float) -> pd.DataFrame:
    max_value = frame[value].max()
    if max_value == 0:
        frame[f"{value}_normalized"] = 0.0
    else:
        frame[f"{value}_normalized"] = np.clip((frame[value] / target) * 100, 0, 100)
    return frame


def normalize_scores(frame: pd.DataFrame, group: str, value: str, config: NormalizationConfig) -> pd.DataFrame:
    if config.mode == "percentile":
        return percentile_normalize(frame, group, value, config)
    if config.mode == "standard":
        if config.standard_target is None:
            raise ValueError("standard_target must be provided for standard normalization")
        return standard_normalize(frame, value, config.standard_target)
    raise ValueError(f"Unknown normalization mode {config.mode}")


__all__ = ["normalize_scores", "NormalizationConfig"]
