"""Numerical stability checks for math kernels."""

from __future__ import annotations

import numpy as np
import pytest

from Urban_Amenities2.math.ces import ces_aggregate
from Urban_Amenities2.math.logsum import nest_inclusive
from Urban_Amenities2.math.satiation import apply_satiation, satiation_weight


def test_ces_handles_mixed_magnitude_inputs() -> None:
    quality = np.ones((1, 3), dtype=float)
    accessibility = np.array([[1e-6, 1.0, 1e6]], dtype=float)
    result = ces_aggregate(quality, accessibility, rho=2.0, axis=1)[0]
    assert np.isfinite(result)
    assert result > 0.0


def test_ces_allows_max_float_inputs() -> None:
    max_float = np.finfo(np.float64).max
    quality = np.ones((1, 2), dtype=float)
    accessibility = np.array([[max_float, max_float]], dtype=float)
    result = ces_aggregate(quality, accessibility, rho=2.0, axis=1)[0]
    assert result == np.finfo(np.float64).max


def test_satiation_large_lambda_underflow_is_safe() -> None:
    weight = float(satiation_weight(1000.0, 10.0))
    assert weight == pytest.approx(0.001, rel=1e-6)


def test_logsum_large_utilities_remain_finite() -> None:
    utilities = np.array([[500.0, 1000.0, 1500.0]])
    inclusive = nest_inclusive(utilities, mu=0.7)
    assert np.all(np.isfinite(inclusive))
