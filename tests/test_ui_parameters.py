"""Tests for UI parameter adjustment helpers."""

from __future__ import annotations

import pytest

from Urban_Amenities2.config.loader import load_params
from Urban_Amenities2.config.params import AUCSParams
from Urban_Amenities2.ui.parameters import ParameterAdjuster


@pytest.fixture(scope="session")
def default_params() -> AUCSParams:
    params_path = "configs/params_default.yml"
    params, _ = load_params(params_path)
    return params


def test_parameter_adjuster_diff(default_params: AUCSParams) -> None:
    adjuster = ParameterAdjuster(default_params)
    adjuster.update_parameter("weight_ea", 25.0)
    diff = adjuster.get_diff()
    assert diff.has_changes()
    assert "weight_ea" in diff.changed_keys


def test_parameter_adjuster_validation(default_params: AUCSParams) -> None:
    adjuster = ParameterAdjuster(default_params)
    for key in ["weight_ea", "weight_lca", "weight_muhaa", "weight_jea", "weight_morr", "weight_cte", "weight_sou"]:
        adjuster.update_parameter(key, adjuster.original_params[key])
    is_valid, message = adjuster.validate_weights()
    assert is_valid
    assert message == ""

    adjuster.update_parameter("weight_sou", 0.0)
    is_valid, message = adjuster.validate_weights()
    assert not is_valid
    assert "Weights sum" in message


def test_parameter_adjuster_reset(default_params: AUCSParams) -> None:
    adjuster = ParameterAdjuster(default_params)
    adjuster.update_parameter("alpha_walk", 0.2)
    adjuster.reset()
    assert adjuster.modified_params == adjuster.original_params
