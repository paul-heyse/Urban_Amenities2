"""Extended coverage for `Urban_Amenities2.math.logsum`."""

from __future__ import annotations

import numpy as np
import pytest

from Urban_Amenities2.math.logsum import (
    ModeUtilityParams,
    mode_utility,
    nest_inclusive,
    time_weighted_accessibility,
    top_level_logsum,
)


def test_nest_inclusive_uses_logsum_exp_for_large_utilities() -> None:
    utilities = np.array([[1000.0, 1001.0, 1002.0]])
    inclusive = nest_inclusive(utilities, mu=1.0)
    expected = 1002.0 + np.log(1.0 + np.exp(-1.0) + np.exp(-2.0))
    assert inclusive.shape == (1,)
    assert inclusive[0] == pytest.approx(expected, rel=1e-9)


def test_top_level_logsum_single_option_equals_utility() -> None:
    inclusive_values = np.array([[5.0], [3.0]])
    result = top_level_logsum(inclusive_values, mu_top=0.7)
    assert np.allclose(result, inclusive_values.squeeze(axis=-1))


def test_logsum_negative_utilities_remain_finite() -> None:
    utilities = np.array([[-5.0, -2.0, -1.0]])
    inclusive = nest_inclusive(utilities, mu=0.5)
    assert np.all(np.isfinite(inclusive))
    top = top_level_logsum(inclusive[:, np.newaxis], mu_top=1.2)
    assert np.all(np.isfinite(top))


def test_mode_utility_combines_costs_and_comfort() -> None:
    params = ModeUtilityParams(beta0=1.0, alpha=0.5, comfort_weight=0.2)
    gtc = np.array([10.0, 20.0], dtype=float)
    comfort = np.array([1.0, -1.0], dtype=float)
    result = mode_utility(gtc, comfort, params)
    expected = params.beta0 - params.alpha * gtc + params.comfort_weight * comfort
    assert np.allclose(result, expected)


def test_time_weighted_accessibility_validates_shape() -> None:
    utilities = np.array([[1.0, 2.0]])
    weights = [0.5]
    with pytest.raises(ValueError):
        time_weighted_accessibility(utilities, weights)


def test_time_weighted_accessibility_tensordot_result() -> None:
    utilities = np.array([[0.0, 1.0, 2.0], [1.5, 0.5, -0.5]], dtype=float)
    weights = np.array([0.2, 0.3, 0.5], dtype=float)
    result = time_weighted_accessibility(utilities, weights)
    expected = np.exp(utilities) @ weights
    assert result.shape == (2,)
    assert np.allclose(result, expected, rtol=1e-12, atol=1e-12)
