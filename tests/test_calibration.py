from __future__ import annotations

import pandas as pd
import pytest

from Urban_Amenities2.calibration.essentials import sensitivity_analysis
from Urban_Amenities2.math.diversity import DiversityConfig
from Urban_Amenities2.scores.essentials_access import (
    EssentialCategoryConfig,
    EssentialsAccessConfig,
)


class StubCalculator:
    def __init__(self, config: EssentialsAccessConfig) -> None:
        self.config = config
        self.calls: list[float] = []

    def compute(self, pois: pd.DataFrame, accessibility: pd.DataFrame):
        rho = self.config.category_params["food"].rho
        self.calls.append(rho)
        frame = pd.DataFrame({"EA": [rho * 10.0]})
        return frame, pd.DataFrame()


def _make_config() -> EssentialsAccessConfig:
    params = {
        "food": EssentialCategoryConfig(
            rho=1.0,
            kappa=1.0,
            diversity=DiversityConfig(weight=1.0),
        )
    }
    return EssentialsAccessConfig(categories=["food"], category_params=params)


def test_sensitivity_analysis_updates_category_parameters() -> None:
    config = _make_config()
    calculator = StubCalculator(config)
    pois = pd.DataFrame({})
    accessibility = pd.DataFrame({})

    result = sensitivity_analysis(
        calculator,
        pois,
        accessibility,
        parameter="rho:food",
        values=[0.5, 2.0],
    )

    assert list(result["value"]) == [0.5, 2.0]
    assert list(result["ea_mean"]) == [5.0, 20.0]
    assert calculator.calls == [0.5, 2.0]
    assert config.category_params["food"].rho == 2.0


def test_sensitivity_analysis_updates_diversity_weight() -> None:
    config = _make_config()
    calculator = StubCalculator(config)
    sensitivity_analysis(
        calculator,
        pd.DataFrame({}),
        pd.DataFrame({}),
        parameter="diversity_weight:food",
        values=[0.25],
    )
    assert config.category_params["food"].diversity.weight == 0.25


def test_sensitivity_analysis_updates_kappa() -> None:
    config = _make_config()
    calculator = StubCalculator(config)
    sensitivity_analysis(
        calculator,
        pd.DataFrame({}),
        pd.DataFrame({}),
        parameter="kappa:food",
        values=[3.5],
    )
    assert config.category_params["food"].kappa == 3.5


def test_sensitivity_analysis_unknown_parameter_raises() -> None:
    config = _make_config()
    calculator = StubCalculator(config)
    with pytest.raises(ValueError):
        sensitivity_analysis(
            calculator,
            pd.DataFrame({}),
            pd.DataFrame({}),
            parameter="unknown",
            values=[1.0],
        )
