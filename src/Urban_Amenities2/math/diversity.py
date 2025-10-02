from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Iterable, Sequence

import math
import numpy as np
import pandas as pd


@dataclass(slots=True)
class DiversityConfig:
    """Configuration for within-category diversity bonuses."""

    weight: float = 1.0
    cap: float = 5.0

    def __post_init__(self) -> None:
        if self.weight < 0:
            raise ValueError("diversity weight must be non-negative")
        if self.cap < 0:
            raise ValueError("diversity cap must be non-negative")


def shannon_entropy(values: Sequence[float]) -> float:
    """Return Shannon entropy for a sequence of non-negative values."""

    array = np.asarray(values, dtype=float)
    positive = array[array > 0]
    if positive.size == 0:
        return 0.0
    total = positive.sum()
    probabilities = positive / total
    entropy = -float(np.sum(probabilities * np.log(probabilities)))
    return max(entropy, 0.0)


def diversity_bonus(values: Sequence[float], weight: float = 1.0, cap: float = 5.0) -> float:
    entropy = shannon_entropy(values)
    bonus = weight * (math.exp(entropy) - 1.0)
    return float(min(max(bonus, 0.0), cap))


def compute_diversity(
    frame: pd.DataFrame,
    value_column: str,
    group_columns: Iterable[str],
    subtype_column: str,
    config: Dict[str, DiversityConfig] | None = None,
) -> pd.DataFrame:
    if value_column not in frame.columns:
        raise KeyError(f"{value_column} column missing from frame")
    if subtype_column not in frame.columns:
        raise KeyError(f"{subtype_column} column missing from frame")
    config = config or {}
    records: list[dict[str, object]] = []
    for keys, group in frame.groupby(list(group_columns)):
        key_dict = dict(zip(group_columns, keys if isinstance(keys, tuple) else (keys,)))
        category = key_dict.get("aucstype") or key_dict.get("category") or "default"
        cfg = config.get(category, DiversityConfig())
        values = group.groupby(subtype_column)[value_column].sum()
        entropy = shannon_entropy(values.values)
        bonus = diversity_bonus(values.values, weight=cfg.weight, cap=cfg.cap)
        records.append({**key_dict, "diversity_bonus": bonus, "entropy": entropy})
    return pd.DataFrame.from_records(records)


__all__ = ["shannon_entropy", "diversity_bonus", "compute_diversity", "DiversityConfig"]
