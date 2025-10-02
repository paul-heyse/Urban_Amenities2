from __future__ import annotations

import pandas as pd


def shortfall_penalty(scores: pd.Series, threshold: float = 20.0, per_miss: float = 2.0, cap: float = 8.0) -> float:
    misses = (scores < threshold).sum()
    penalty = min(misses * per_miss, cap)
    return float(penalty)


__all__ = ["shortfall_penalty"]
