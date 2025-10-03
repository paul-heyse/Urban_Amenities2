"""Extended coverage for `Urban_Amenities2.math.ces`."""

from __future__ import annotations

import numpy as np
import pytest
from numpy.exceptions import AxisError
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from Urban_Amenities2.math.ces import MAX_RHO, ces_aggregate, compute_z
from tests.fixtures.math_samples import CES_REGRESSION_VECTORS
from tests.math.strategies import ces_inputs, elasticity_params, scale_factors


def _as_row(values: list[float]) -> np.ndarray:
    return np.asarray(values, dtype=float)[np.newaxis, :]


def test_ces_cobb_douglas_limit() -> None:
    quality = _as_row([2.0, 8.0])
    accessibility = np.ones_like(quality)
    result = ces_aggregate(quality, accessibility, rho=1e-6, axis=1)[0]
    assert result == pytest.approx(4.0, rel=1e-2)


def test_ces_linear_aggregation_returns_mean() -> None:
    accessibility_values = np.asarray([10.0, 20.0, 30.0], dtype=float)
    quality = np.ones((1, 3), dtype=float)
    # Normalise accessibility so the linear case returns the arithmetic mean.
    accessibility = (accessibility_values / accessibility_values.size)[np.newaxis, :]
    result = ces_aggregate(quality, accessibility, rho=1.0, axis=1)[0]
    assert result == pytest.approx(20.0, rel=1e-12)


def test_ces_complementary_goods_below_minimum() -> None:
    values = np.asarray([10.0, 20.0], dtype=float)
    quality = np.ones((1, values.size), dtype=float)
    result = ces_aggregate(quality, values[np.newaxis, :], rho=-1.0, axis=1)[0]
    assert result < values.min()


def test_ces_near_perfect_substitutes_matches_max() -> None:
    values = np.asarray([5.0, 10.0, 15.0], dtype=float)
    quality = np.ones((1, values.size), dtype=float)
    result = ces_aggregate(quality, values[np.newaxis, :], rho=MAX_RHO, axis=1)[0]
    assert result == pytest.approx(values.max(), rel=1e-2)


def test_ces_handles_large_values_without_overflow() -> None:
    large = np.full(3, 1e300, dtype=float)
    quality = np.ones((1, 3), dtype=float)
    result = ces_aggregate(quality, large[np.newaxis, :], rho=2.0, axis=1)[0]
    expected = np.sqrt(3.0) * 1e300
    assert np.isfinite(result)
    assert result == pytest.approx(expected, rel=1e-9)


def test_ces_handles_small_values_without_underflow() -> None:
    tiny = np.full(2, 1e-300, dtype=float)
    quality = np.ones((1, 2), dtype=float)
    result = ces_aggregate(quality, tiny[np.newaxis, :], rho=2.0, axis=1)[0]
    expected = np.sqrt(2.0) * 1e-300
    assert result == pytest.approx(expected, rel=1e-9, abs=0.0)


def test_ces_invalid_axis_raises() -> None:
    quality = np.ones((2, 2), dtype=float)
    accessibility = np.ones((2, 2), dtype=float)
    with pytest.raises(AxisError):
        ces_aggregate(quality, accessibility, rho=0.5, axis=5)


def test_ces_mismatched_shapes_raise() -> None:
    quality = np.ones((1, 3), dtype=float)
    accessibility = np.ones((1, 2), dtype=float)
    with pytest.raises(ValueError, match="quality and accessibility"):
        ces_aggregate(quality, accessibility, rho=0.5, axis=1)


def test_ces_nonfinite_rho_rejected() -> None:
    quality = np.ones((1, 2), dtype=float)
    accessibility = np.ones((1, 2), dtype=float)
    with pytest.raises(ValueError, match="rho must be finite"):
        ces_aggregate(quality, accessibility, rho=np.inf, axis=1)


def test_ces_zero_scale_returns_zero() -> None:
    quality = np.zeros((1, 3), dtype=float)
    accessibility = np.ones((1, 3), dtype=float)
    result = ces_aggregate(quality, accessibility, rho=2.0, axis=1)
    assert np.all(result == 0.0)


def test_ces_negative_rho_without_zeros() -> None:
    quality = np.array([[2.0, 3.0, 4.0]], dtype=float)
    accessibility = np.array([[0.5, 1.0, 1.5]], dtype=float)
    result = ces_aggregate(quality, accessibility, rho=-0.5, axis=1)
    assert np.isfinite(result[0])


def test_ces_rho_above_limit_raises() -> None:
    quality = np.ones((1, 2), dtype=float)
    accessibility = np.ones((1, 2), dtype=float)
    with pytest.raises(ValueError, match="less than or equal"):
        ces_aggregate(quality, accessibility, rho=MAX_RHO + 0.1, axis=1)


def test_ces_empty_inputs_return_zero_vector() -> None:
    quality = np.empty((2, 0), dtype=float)
    accessibility = np.empty((2, 0), dtype=float)
    result = ces_aggregate(quality, accessibility, rho=0.5, axis=-1)
    assert result.shape == (2,)
    assert np.all(result == 0.0)


def test_ces_empty_inputs_with_explicit_axis() -> None:
    quality = np.empty((0, 3), dtype=float)
    accessibility = np.empty((0, 3), dtype=float)
    result = ces_aggregate(quality, accessibility, rho=0.4, axis=0)
    assert result.shape == (3,)
    assert np.all(result == 0.0)


def test_compute_z_power_branch_produces_float64() -> None:
    quality = np.array([[0.5, 1.0, 1.5]], dtype=float)
    accessibility = np.array([[1.0, 0.5, 0.25]], dtype=float)
    powered = compute_z.py_func(quality, accessibility, rho=0.5)
    assert powered.dtype == np.float64
    assert np.all(powered >= 0.0)


def test_compute_z_linear_branch_uses_product() -> None:
    quality = np.array([[1.5, 2.5, 3.5]], dtype=float)
    accessibility = np.array([[0.2, 0.4, 0.6]], dtype=float)
    linear = compute_z.py_func(quality, accessibility, rho=1.0 - 5e-7)
    assert linear.dtype == np.float64
    assert np.allclose(linear, quality * accessibility)


@pytest.mark.parametrize(
    "quality_values, accessibility_values, rho, expected, rtol",
    CES_REGRESSION_VECTORS,
)
def test_ces_regression_vectors(
    quality_values: list[float],
    accessibility_values: list[float],
    rho: float,
    expected: float,
    rtol: float,
) -> None:
    quality = _as_row(quality_values)
    accessibility = _as_row(accessibility_values)
    result = ces_aggregate(quality, accessibility, rho=rho, axis=1)[0]
    assert result == pytest.approx(expected, rel=rtol)


@settings(deadline=None, max_examples=120)
@given(values=ces_inputs, rho=elasticity_params)
def test_ces_monotonicity_property(values: list[float], rho: float) -> None:
    arr = np.asarray(values, dtype=float)
    base = ces_aggregate(np.ones((1, arr.size)), arr[np.newaxis, :], rho=rho, axis=1)[0]
    scaled = ces_aggregate(
        np.ones((1, arr.size)),
        (arr * 1.1)[np.newaxis, :],
        rho=rho,
        axis=1,
    )[0]
    assert scaled >= base - 1e-8


@settings(deadline=None, max_examples=120)
@given(values=ces_inputs, rho=elasticity_params, factor=scale_factors)
def test_ces_homogeneity_property(
    values: list[float], rho: float, factor: float
) -> None:
    arr = np.asarray(values, dtype=float)
    base = ces_aggregate(np.ones((1, arr.size)), arr[np.newaxis, :], rho=rho, axis=1)[0]
    assume(np.isfinite(base))
    assume(base > 0)
    assume(base * factor < np.finfo(np.float64).max / 2)
    scaled = ces_aggregate(
        np.ones((1, arr.size)),
        (arr * factor)[np.newaxis, :],
        rho=rho,
        axis=1,
    )[0]
    assert scaled == pytest.approx(factor * base, rel=1e-6, abs=1e-6)


@settings(deadline=None, max_examples=120)
@given(values=ces_inputs, rho=st.floats(min_value=0.1, max_value=MAX_RHO, allow_nan=False, allow_infinity=False))
def test_ces_respects_upper_bound_for_normalised_inputs(
    values: list[float], rho: float
) -> None:
    arr = np.asarray(values, dtype=float)
    assume(np.all(arr > 0))
    normalised = (arr / arr.sum())[np.newaxis, :]
    result = ces_aggregate(
        np.ones((1, arr.size)),
        normalised,
        rho=rho,
        axis=1,
    )[0]
    if rho >= 1.0:
        assert normalised.max() - 1e-8 <= result <= 1.0 + 1e-8
    else:
        assert result >= 1.0 - 1e-8
