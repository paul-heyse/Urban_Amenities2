from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, TypeVar

import numpy as np
from numpy.exceptions import AxisError
from numpy.typing import NDArray

if TYPE_CHECKING:  # pragma: no cover - typing helper for numba decorator
    _F = TypeVar("_F", bound=Callable[..., NDArray[np.float64]])

    def njit(*args: object, **kwargs: object) -> Callable[[_F], _F]: ...

else:
    from numba import njit  # type: ignore[import-untyped]

from ..logging_utils import get_logger

LOGGER = get_logger("aucs.math.ces")
EPSILON = 1e-12
_LINEAR_TOL = 1e-6
_GEOMETRIC_TOL = 1e-6
MAX_RHO = 10.0


def _axis_index(array: NDArray[np.float64], axis: int) -> int:
    axis_index = axis if axis >= 0 else array.ndim + axis
    if axis_index < 0 or axis_index >= array.ndim:
        raise AxisError(axis, array.ndim)
    return axis_index


def _expand_for_axis(values: NDArray[np.float64], axis: int) -> NDArray[np.float64]:
    return np.expand_dims(values, axis=axis)


def _aggregate_positive_rho(
    product: NDArray[np.float64],
    rho: float,
    axis: int,
) -> NDArray[np.float64]:
    non_negative = np.maximum(product, 0.0)
    axis_index = _axis_index(non_negative, axis)
    scale = np.max(non_negative, axis=axis_index)
    scale_expanded = _expand_for_axis(scale, axis_index)
    safe_scale = np.where(scale_expanded > 0.0, scale_expanded, 1.0)
    scaled = non_negative / safe_scale
    with np.errstate(divide="ignore", invalid="ignore"):
        powered = np.power(scaled, rho)
    summed = np.sum(powered, axis=axis_index)
    base = np.power(np.clip(summed, 0.0, None), 1.0 / rho)
    result = base * scale
    max_float = np.finfo(np.float64).max
    clipped = np.minimum(result, max_float)
    return np.asarray(np.where(scale > 0.0, clipped, 0.0), dtype=float)


def _aggregate_negative_rho(
    product: NDArray[np.float64],
    rho: float,
    axis: int,
) -> NDArray[np.float64]:
    non_negative = np.maximum(product, 0.0)
    axis_index = _axis_index(non_negative, axis)
    zero_mask = np.any(non_negative == 0.0, axis=axis_index)
    positive = np.where(non_negative > 0.0, non_negative, np.inf)
    scale = np.min(positive, axis=axis_index)
    scale = np.where(np.isfinite(scale), scale, 0.0)
    scale_expanded = _expand_for_axis(scale, axis_index)
    safe_scale = np.where(scale_expanded > 0.0, scale_expanded, 1.0)
    scaled = non_negative / safe_scale
    with np.errstate(divide="ignore", invalid="ignore"):
        powered = np.power(np.where(scaled > 0.0, scaled, np.inf), rho)
    summed = np.sum(powered, axis=axis_index)
    base = np.power(np.clip(summed, 0.0, None), 1.0 / rho)
    result = base * scale
    max_float = np.finfo(np.float64).max
    cleaned = np.where(zero_mask, 0.0, result)
    clipped = np.minimum(cleaned, max_float)
    return np.asarray(np.where(np.isfinite(clipped), clipped, 0.0), dtype=float)


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
    if rho > MAX_RHO:
        raise ValueError(f"rho must be less than or equal to {MAX_RHO}")
    return quality_typed, accessibility_typed


@njit(cache=True)
def compute_z(
    quality: NDArray[np.float64],
    accessibility: NDArray[np.float64],
    rho: float,
) -> NDArray[np.float64]:
    product = quality * accessibility
    non_negative = np.maximum(product, 0.0)
    product64 = non_negative.astype(np.float64)
    if abs(rho - 1.0) < _LINEAR_TOL:
        return product64
    powered = np.power(product64, rho)
    return powered.astype(np.float64)


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
    axis_index = axis if axis >= 0 else product.ndim + axis
    if abs(rho) <= _GEOMETRIC_TOL:
        result = _geometric_mean(product, axis_index)
    elif abs(rho - 1.0) < _LINEAR_TOL:
        result = np.sum(np.maximum(product, 0.0), axis=axis_index)
    elif rho > 0:
        result = _aggregate_positive_rho(product, rho, axis_index)
    else:
        result = _aggregate_negative_rho(product, rho, axis_index)

    LOGGER.debug(
        "ces_aggregate",
        rho=float(rho),
        count=int(product.size),
        axis=axis,
        min=float(np.min(result)) if np.size(result) else 0.0,
        max=float(np.max(result)) if np.size(result) else 0.0,
        mean=float(np.mean(result)) if np.size(result) else 0.0,
    )
    return np.asarray(result, dtype=float)


__all__ = ["MAX_RHO", "ces_aggregate", "compute_z"]
