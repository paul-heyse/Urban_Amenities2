"""Regression coverage for `Urban_Amenities2.math.gtc`."""

from __future__ import annotations

import numpy as np
import pytest

from Urban_Amenities2.math.gtc import GTCParameters, generalized_travel_cost


def test_generalized_travel_cost_combines_components() -> None:
    params = GTCParameters(
        theta_iv=1.2,
        theta_wait=0.8,
        theta_walk=0.5,
        transfer_penalty=4.0,
        reliability_weight=0.3,
        value_of_time=20.0,
        carry_penalty=1.5,
    )
    result = generalized_travel_cost(
        in_vehicle=np.array([10.0, 5.0]),
        wait=np.array([2.0, 1.0]),
        walk=np.array([1.0, 0.5]),
        transfers=np.array([1.0, 0.0]),
        reliability=np.array([3.0, 1.0]),
        fare=np.array([4.0, 6.0]),
        params=params,
        carry_adjustment=np.array([0.5, 1.0]),
    )
    expected = (
        params.theta_iv * np.array([10.0, 5.0])
        + params.theta_wait * np.array([2.0, 1.0])
        + params.theta_walk * np.array([1.0, 0.5])
        + params.transfer_penalty * np.array([1.0, 0.0])
        + params.reliability_weight * np.array([3.0, 1.0])
        + np.array([4.0, 6.0]) / params.value_of_time
        + params.carry_penalty
        + np.array([0.5, 1.0])
    )
    assert np.allclose(result, expected)
    assert result.dtype == float


def test_generalized_travel_cost_handles_zero_value_of_time() -> None:
    params = GTCParameters(
        theta_iv=1.0,
        theta_wait=1.0,
        theta_walk=1.0,
        transfer_penalty=0.0,
        reliability_weight=0.0,
        value_of_time=0.0,
        carry_penalty=0.0,
    )
    result = generalized_travel_cost(
        in_vehicle=np.array([1.0]),
        wait=np.array([1.0]),
        walk=np.array([1.0]),
        transfers=np.array([0.0]),
        reliability=np.array([0.0]),
        fare=np.array([10.0]),
        params=params,
    )
    expected = np.array([3.0 + 10.0])
    assert np.allclose(result, expected)


def test_generalized_travel_cost_scalar_adjustment_broadcasts() -> None:
    params = GTCParameters(
        theta_iv=0.5,
        theta_wait=0.5,
        theta_walk=0.5,
        transfer_penalty=0.5,
        reliability_weight=0.5,
        value_of_time=30.0,
        carry_penalty=2.0,
    )
    result = generalized_travel_cost(
        in_vehicle=np.array([2.0]),
        wait=np.array([2.0]),
        walk=np.array([2.0]),
        transfers=np.array([2.0]),
        reliability=np.array([2.0]),
        fare=np.array([3.0]),
        params=params,
        carry_adjustment=1.0,
    )
    assert result.shape == (1,)
    expected = (
        params.theta_iv * 2.0
        + params.theta_wait * 2.0
        + params.theta_walk * 2.0
        + params.transfer_penalty * 2.0
        + params.reliability_weight * 2.0
        + 3.0 / params.value_of_time
        + params.carry_penalty
        + 1.0
    )
    assert pytest.approx(result[0], rel=1e-9) == expected

