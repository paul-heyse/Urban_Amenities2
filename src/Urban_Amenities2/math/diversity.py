from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Iterable

import pandas as pd


@dataclass
class DiversityConfig:
    weight: float = 1.0
    cap: float = 5.0


def shannon_entropy(values: Iterable[float]) -> float:
    total = float(sum(values))
    if total <= 0:
        return 0.0
    entropy = 0.0
    for value in values:
        if value <= 0:
            continue
        p = value / total
        entropy -= p * math.log(p)
    return entropy


def diversity_bonus(values: Iterable[float], weight: float = 1.0, cap: float = 5.0) -> float:
    entropy = shannon_entropy(values)
    bonus = weight * (math.exp(entropy) - 1.0)
    return float(min(bonus, cap))


def compute_diversity(
    frame: pd.DataFrame,
    value_column: str,
    group_columns: Iterable[str],
    subtype_column: str,
    config: Dict[str, DiversityConfig],
) -> pd.DataFrame:
    records = []
    for keys, group in frame.groupby(list(group_columns)):
        key_dict = dict(zip(group_columns, keys))
        category = key_dict.get("aucstype") or key_dict.get("category") or "default"
        cfg = config.get(category, DiversityConfig())
        values = group.groupby(subtype_column)[value_column].sum()
        bonus = diversity_bonus(values.values, weight=cfg.weight, cap=cfg.cap)
        records.append({**key_dict, "diversity_bonus": bonus, "entropy": shannon_entropy(values.values)})
    return pd.DataFrame.from_records(records)


__all__ = ["shannon_entropy", "diversity_bonus", "compute_diversity", "DiversityConfig"]
