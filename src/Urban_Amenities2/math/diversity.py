from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
import math

import numpy as np
from numpy.typing import NDArray
import pandas as pd


@dataclass(slots=True)
class DiversityConfig:
    """Configuration for within-category diversity bonuses."""

    weight: float = 0.2
    min_multiplier: float = 1.0
    max_multiplier: float = 1.2
    cap: float | None = None

    def __post_init__(self) -> None:
        if self.weight < 0:
            raise ValueError("diversity weight must be non-negative")
        if self.min_multiplier <= 0:
            raise ValueError("min_multiplier must be positive")
        if self.max_multiplier < self.min_multiplier:
            raise ValueError("max_multiplier must be >= min_multiplier")
        if self.cap is not None:
            if self.cap < 0:
                raise ValueError("cap must be non-negative")
            self.max_multiplier = min(self.max_multiplier, self.min_multiplier + self.cap)


def shannon_entropy(values: Sequence[float] | NDArray[np.float64]) -> float:
    """Return Shannon entropy for a sequence of non-negative values."""

    array = np.asarray(values, dtype=float)
    positive = array[array > 0]
    if positive.size == 0:
        return 0.0
    total = positive.sum()
    probabilities = positive / total
    entropy = -float(np.sum(probabilities * np.log(probabilities)))
    return max(entropy, 0.0)


def _normalised_entropy(values: Sequence[float] | NDArray[np.float64]) -> float:
    array = np.asarray(values, dtype=float)
    positive = array[array > 0]
    if positive.size <= 1:
        return 0.0
    entropy = shannon_entropy(positive)
    max_entropy = math.log(positive.size)
    if max_entropy <= 0:
        return 0.0
    return float(min(entropy / max_entropy, 1.0))


def diversity_multiplier(
    values: Sequence[float] | NDArray[np.float64],
    config: DiversityConfig | None = None,
) -> float:
    cfg = config or DiversityConfig()
    norm_entropy = _normalised_entropy(values)
    bonus = cfg.weight * norm_entropy
    multiplier = cfg.min_multiplier + bonus
    return float(min(max(multiplier, cfg.min_multiplier), cfg.max_multiplier))


def compute_diversity(
    frame: pd.DataFrame,
    value_column: str,
    group_columns: Iterable[str],
    subtype_column: str,
    config: dict[str, DiversityConfig] | None = None,
) -> pd.DataFrame:
    if value_column not in frame.columns:
        raise KeyError(f"{value_column} column missing from frame")
    if subtype_column not in frame.columns:
        raise KeyError(f"{subtype_column} column missing from frame")
    config = config or {}
    records: list[dict[str, object]] = []
    for keys, group in frame.groupby(list(group_columns)):
        key_dict = dict(zip(group_columns, keys if isinstance(keys, tuple) else (keys,), strict=False))
        category = key_dict.get("aucstype") or key_dict.get("category") or "default"
        cfg = config.get(category, DiversityConfig())
        values = group.groupby(subtype_column)[value_column].sum()
        entropy = shannon_entropy(values.values)
        multiplier = diversity_multiplier(values.values, cfg)
        records.append({**key_dict, "diversity_multiplier": multiplier, "entropy": entropy})
    return pd.DataFrame.from_records(records)


# Backwards compatibility alias
diversity_bonus = diversity_multiplier


__all__ = [
    "DiversityConfig",
    "compute_diversity",
    "diversity_bonus",
    "diversity_multiplier",
    "shannon_entropy",
]
