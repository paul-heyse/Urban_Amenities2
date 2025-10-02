from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass
class ModeUtilityParams:
    beta0: float
    alpha: float
    comfort_weight: float = 0.0


def mode_utility(gtc: np.ndarray, comfort: np.ndarray, params: ModeUtilityParams) -> np.ndarray:
    return params.beta0 - params.alpha * gtc + params.comfort_weight * comfort


def nest_inclusive(utilities: np.ndarray, mu: float) -> np.ndarray:
    scaled = utilities / mu
    max_util = np.max(scaled, axis=-1, keepdims=True)
    stable = scaled - max_util
    logsum = max_util + np.log(np.sum(np.exp(stable), axis=-1, keepdims=True))
    return mu * np.squeeze(logsum, axis=-1)


def top_level_logsum(inclusive_values: np.ndarray, mu_top: float) -> np.ndarray:
    scaled = inclusive_values / mu_top
    max_val = np.max(scaled, axis=-1, keepdims=True)
    stable = scaled - max_val
    logsum = max_val + np.log(np.sum(np.exp(stable), axis=-1, keepdims=True))
    return mu_top * np.squeeze(logsum, axis=-1)


def time_weighted_accessibility(utilities: np.ndarray, weights: Sequence[float]) -> np.ndarray:
    weights = np.asarray(weights, dtype=float)
    if utilities.shape[-1] != len(weights):
        raise ValueError("utilities last dimension must match weight vector length")
    exp_utilities = np.exp(utilities)
    return np.tensordot(exp_utilities, weights, axes=([-1], [0]))


__all__ = ["mode_utility", "nest_inclusive", "top_level_logsum", "ModeUtilityParams", "time_weighted_accessibility"]
