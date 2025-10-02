from __future__ import annotations

import numpy as np
from numba import njit

EPSILON = 1e-12


@njit(cache=True)
def compute_z(quality: np.ndarray, accessibility: np.ndarray, rho: float) -> np.ndarray:
    product = np.maximum(quality * accessibility, 0.0)
    if rho == 1.0:
        return product
    return np.power(product, rho)


def ces_aggregate(quality: np.ndarray, accessibility: np.ndarray, rho: float, axis: int = -1) -> np.ndarray:
    quality = np.asarray(quality, dtype=float)
    accessibility = np.asarray(accessibility, dtype=float)
    if quality.shape != accessibility.shape:
        raise ValueError("quality and accessibility arrays must have the same shape")
    if quality.size == 0:
        return np.zeros(quality.shape[:axis if axis != -1 else 0])
    if abs(rho) < 1e-9:
        log_values = np.log(np.clip(quality * accessibility, EPSILON, None))
        return np.exp(log_values.mean(axis=axis))
    z = compute_z(quality, accessibility, rho)
    summed = np.sum(z, axis=axis)
    with np.errstate(divide="ignore", invalid="ignore"):
        result = np.power(np.clip(summed, 0.0, None), 1.0 / rho)
    result[np.isnan(result)] = 0.0
    return result


__all__ = ["ces_aggregate", "compute_z"]
