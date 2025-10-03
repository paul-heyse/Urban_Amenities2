from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, TypeVar

import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:  # pragma: no cover - typing helper for numba decorator
    _F = TypeVar("_F", bound=Callable[..., NDArray[np.float64]])

    def njit(*args: object, **kwargs: object) -> Callable[[_F], _F]:
        ...

else:
    from numba import njit  # type: ignore[import-untyped]

from ..logging_utils import get_logger

LOGGER = get_logger("aucs.math.ces")
EPSILON = 1e-12
_LINEAR_TOL = 1e-6
_GEOMETRIC_TOL = 1e-6


def _validate_inputs(
    quality: NDArray[np.float64] | float | Sequence[float],
    accessibility: NDArray[np.float64] | float | Sequence[float],
    rho: float,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    quality_array = np.asarray(quality, dtype=float)
    accessibility_array = np.asarray(accessibility, dtype=float)
    quality_typed: NDArray[np.float64] = quality_array
    accessibility_typed: NDArray[np.float64] = accessibility_array
    if quality_array.shape != accessibility_array.shape:
        raise ValueError("quality and accessibility arrays must have the same shape")
    if not np.isfinite(rho):
        raise ValueError("rho must be finite")
    if rho > 1.0:
        raise ValueError("rho must be less than or equal to 1 for CES aggregation")
    return quality_typed, accessibility_typed


@njit(cache=True)
def compute_z(
    quality: NDArray[np.float64],
    accessibility: NDArray[np.float64],
    rho: float,
) -> NDArray[np.float64]:
    product: NDArray[np.float64] = np.asarray(
        np.maximum(quality * accessibility, 0.0), dtype=float
    )
    if abs(rho - 1.0) < _LINEAR_TOL:
        return product
    powered: NDArray[np.float64] = np.asarray(
        np.power(np.clip(product, 0.0, None), rho), dtype=float
    )
    return powered


def _geometric_mean(product: NDArray[np.float64], axis: int) -> NDArray[np.float64]:
    log_values = np.log(np.clip(product, EPSILON, None))
    return np.asarray(np.exp(log_values.mean(axis=axis)), dtype=float)


def ces_aggregate(
    quality: NDArray[np.float64] | Sequence[float],
    accessibility: NDArray[np.float64] | Sequence[float],
    rho: float,
    axis: int = -1,
) -> NDArray[np.float64]:
    quality_array, accessibility_array = _validate_inputs(quality, accessibility, rho)
    if quality_array.size == 0:
        shape = list(quality_array.shape)
        if axis < 0:
            axis = quality_array.ndim + axis
        if 0 <= axis < len(shape):
            shape.pop(axis)
        empty = np.zeros(shape, dtype=float)
        return empty

    product = quality_array * accessibility_array
    if abs(rho) < _GEOMETRIC_TOL:
        result = _geometric_mean(product, axis)
    elif abs(rho - 1.0) < _LINEAR_TOL:
        result = np.sum(product, axis=axis)
    else:
        z = compute_z(quality_array, accessibility_array, rho)
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
    return np.asarray(result, dtype=float)


__all__ = ["ces_aggregate", "compute_z"]
