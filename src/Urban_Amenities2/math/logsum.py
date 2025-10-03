from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(slots=True)
class ModeUtilityParams:
    beta0: float
    alpha: float
    comfort_weight: float = 0.0


def mode_utility(
    gtc: NDArray[np.float64],
    comfort: NDArray[np.float64],
    params: ModeUtilityParams,
) -> NDArray[np.float64]:
    result = params.beta0 - params.alpha * gtc + params.comfort_weight * comfort
    return np.asarray(result, dtype=float)


def nest_inclusive(utilities: NDArray[np.float64], mu: float) -> NDArray[np.float64]:
    scaled = utilities / mu
    max_util = np.max(scaled, axis=-1, keepdims=True)
    stable = scaled - max_util
    logsum = max_util + np.log(np.sum(np.exp(stable), axis=-1, keepdims=True))
    return np.asarray(mu * np.squeeze(logsum, axis=-1), dtype=float)


def top_level_logsum(
    inclusive_values: NDArray[np.float64],
    mu_top: float,
) -> NDArray[np.float64]:
    scaled = inclusive_values / mu_top
    max_val = np.max(scaled, axis=-1, keepdims=True)
    stable = scaled - max_val
    logsum = max_val + np.log(np.sum(np.exp(stable), axis=-1, keepdims=True))
    return np.asarray(mu_top * np.squeeze(logsum, axis=-1), dtype=float)


def time_weighted_accessibility(
    utilities: NDArray[np.float64],
    weights: Sequence[float],
) -> NDArray[np.float64]:
    weights_array = np.asarray(weights, dtype=float)
    if utilities.shape[-1] != len(weights):
        raise ValueError("utilities last dimension must match weight vector length")
    exp_utilities = np.exp(utilities)
    return np.asarray(np.tensordot(exp_utilities, weights_array, axes=([-1], [0])), dtype=float)


__all__ = ["mode_utility", "nest_inclusive", "top_level_logsum", "ModeUtilityParams", "time_weighted_accessibility"]
