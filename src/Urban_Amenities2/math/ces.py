from __future__ import annotations

import numpy as np
from numba import njit

from ..logging_utils import get_logger

LOGGER = get_logger("aucs.math.ces")
EPSILON = 1e-12
_LINEAR_TOL = 1e-6
_GEOMETRIC_TOL = 1e-6


def _validate_inputs(quality: np.ndarray, accessibility: np.ndarray, rho: float) -> tuple[np.ndarray, np.ndarray]:
    quality = np.asarray(quality, dtype=float)
    accessibility = np.asarray(accessibility, dtype=float)
    if quality.shape != accessibility.shape:
        raise ValueError("quality and accessibility arrays must have the same shape")
    if not np.isfinite(rho):
        raise ValueError("rho must be finite")
    if rho > 1.0:
        raise ValueError("rho must be less than or equal to 1 for CES aggregation")
    return quality, accessibility


@njit(cache=True)
def compute_z(quality: np.ndarray, accessibility: np.ndarray, rho: float) -> np.ndarray:
    product = np.maximum(quality * accessibility, 0.0)
    if abs(rho - 1.0) < _LINEAR_TOL:
        return product
    return np.power(np.clip(product, 0.0, None), rho)


def _geometric_mean(product: np.ndarray, axis: int) -> np.ndarray:
    log_values = np.log(np.clip(product, EPSILON, None))
    return np.exp(log_values.mean(axis=axis))


def ces_aggregate(quality: np.ndarray, accessibility: np.ndarray, rho: float, axis: int = -1) -> np.ndarray:
    quality, accessibility = _validate_inputs(quality, accessibility, rho)
    if quality.size == 0:
        shape = list(quality.shape)
        if axis < 0:
            axis = quality.ndim + axis
        shape.pop(axis)
        return np.zeros(shape, dtype=float)

    product = quality * accessibility
    if abs(rho) < _GEOMETRIC_TOL:
        result = _geometric_mean(product, axis)
    elif abs(rho - 1.0) < _LINEAR_TOL:
        result = np.sum(product, axis=axis)
    else:
        z = compute_z(quality, accessibility, rho)
        summed = np.sum(z, axis=axis)
        with np.errstate(divide="ignore", invalid="ignore"):
            result = np.power(np.clip(summed, 0.0, None), 1.0 / rho)
        result = np.where(np.isfinite(result), result, 0.0)

    LOGGER.debug(
        "ces_aggregate",
        rho=float(rho),
        count=int(product.size),
        axis=axis,
        min=float(np.min(result)),
        max=float(np.max(result)),
        mean=float(np.mean(result)) if result.size else 0.0,
    )
    return result


__all__ = ["ces_aggregate", "compute_z"]
