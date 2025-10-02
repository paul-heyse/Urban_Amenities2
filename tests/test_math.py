import numpy as np
import pandas as pd
import numpy as np
import pandas as pd
import pytest

from Urban_Amenities2.math.ces import ces_aggregate, compute_z
from Urban_Amenities2.math.diversity import DiversityConfig, compute_diversity, diversity_multiplier
from Urban_Amenities2.math.gtc import GTCParameters, generalized_travel_cost
from Urban_Amenities2.math.satiation import apply_satiation, compute_kappa_from_anchor
from Urban_Amenities2.scores.penalties import shortfall_penalty


def test_ces_known_output() -> None:
    quality = np.array([[1.0, 0.5]])
    accessibility = np.array([[1.0, 1.0]])
    z = compute_z(quality, accessibility, rho=1.0)
    assert np.allclose(z, quality * accessibility)
    result = ces_aggregate(quality, accessibility, rho=1.0, axis=1)
    assert pytest.approx(result[0]) == 1.5


def test_ces_monotonicity() -> None:
    base_quality = np.array([[0.5, 0.5]])
    better_quality = np.array([[0.6, 0.5]])
    accessibility = np.array([[1.0, 1.0]])
    base = ces_aggregate(base_quality, accessibility, rho=0.5, axis=1)
    improved = ces_aggregate(better_quality, accessibility, rho=0.5, axis=1)
    assert improved[0] >= base[0]


def test_generalized_travel_cost_components() -> None:
    params = GTCParameters(
        theta_iv=1.0,
        theta_wait=2.0,
        theta_walk=3.0,
        transfer_penalty=5.0,
        reliability_weight=0.5,
        value_of_time=30.0,
        carry_penalty=1.0,
    )
    cost = generalized_travel_cost(
        in_vehicle=np.array([10.0]),
        wait=np.array([5.0]),
        walk=np.array([2.0]),
        transfers=np.array([1.0]),
        reliability=np.array([4.0]),
        fare=np.array([6.0]),
        params=params,
        carry_adjustment=np.array([0.5]),
    )
    expected = 10.0 + 10.0 + 6.0 + 5.0 + 2.0 + (6.0 / 30.0) + 1.0 + 0.5
    assert pytest.approx(cost[0]) == expected


def test_satiation_anchor() -> None:
    kappa = compute_kappa_from_anchor(70, 2.0)
    values = np.array([2.0])
    result = apply_satiation(values, kappa)
    assert pytest.approx(result[0], rel=1e-3) == 70


def test_satiation_asymptote() -> None:
    values = np.linspace(0, 50, 100)
    scores = apply_satiation(values, 0.2)
    assert scores.max() <= 100
    assert scores[-1] > 99


def test_diversity_multiplier_and_compute() -> None:
    values = [10.0, 5.0, 5.0]
    config = DiversityConfig(weight=0.3, min_multiplier=1.0, max_multiplier=1.2)
    multiplier = diversity_multiplier(values, config)
    assert 1.0 <= multiplier <= config.max_multiplier
    frame = pd.DataFrame(
        {
            "hex_id": ["hex1", "hex1", "hex1"],
            "category": ["grocery"] * 3,
            "subtype": ["a", "b", "c"],
            "qw": values,
        }
    )
    config_map = {"grocery": config}
    diversity = compute_diversity(frame, "qw", ["hex_id", "category"], "subtype", config_map)
    assert pytest.approx(diversity.loc[0, "diversity_multiplier"], rel=1e-6) == multiplier


def test_shortfall_penalty_cap() -> None:
    scores = pd.Series([10, 15, 30])
    penalty = shortfall_penalty(scores, threshold=20, per_miss=3, cap=5)
    assert penalty == 5
