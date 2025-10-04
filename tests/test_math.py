import numpy as np
import pandas as pd
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st
from hypothesis.extra.numpy import arrays

from Urban_Amenities2.math.ces import MAX_RHO, ces_aggregate, compute_z
from Urban_Amenities2.math.diversity import DiversityConfig, compute_diversity, diversity_multiplier
from Urban_Amenities2.math.gtc import GTCParameters, generalized_travel_cost
from Urban_Amenities2.math.logsum import (
    ModeUtilityParams,
    mode_utility,
    nest_inclusive,
    time_weighted_accessibility,
    top_level_logsum,
)
from Urban_Amenities2.math.satiation import apply_satiation, compute_kappa_from_anchor
from Urban_Amenities2.scores.penalties import shortfall_penalty


def test_ces_known_output() -> None:
    quality = np.array([[1.0, 0.5]])
    accessibility = np.array([[1.0, 1.0]])
    z = compute_z(quality, accessibility, rho=1.0)
    assert np.allclose(z, quality * accessibility)
    result = ces_aggregate(quality, accessibility, rho=1.0, axis=1)
    assert pytest.approx(result[0]) == 1.5


def test_compute_z_returns_float64_and_non_negative() -> None:
    quality = np.array([[0.8, 1.2], [0.0, 2.5]], dtype=np.float32)
    accessibility = np.array([[0.5, 0.3], [1.5, 0.0]], dtype=np.float32)
    result = compute_z(quality, accessibility, rho=0.7)
    assert result.dtype == np.float64
    assert result.shape == quality.shape
    assert np.all(result >= 0.0)


def test_compute_z_compiles_numba_and_accepts_lists() -> None:
    quality = [[0.6, 0.2, 0.1]]
    accessibility = [[1.5, 0.5, 0.25]]
    values = compute_z(
        np.asarray(quality, dtype=float), np.asarray(accessibility, dtype=float), rho=0.5
    )
    assert values.shape == (1, 3)
    assert np.all(np.isfinite(values))
    assert getattr(compute_z, "signatures", [])  # numba registers signatures after compilation


def test_ces_monotonicity() -> None:
    base_quality = np.array([[0.5, 0.5]])
    better_quality = np.array([[0.6, 0.5]])
    accessibility = np.array([[1.0, 1.0]])
    base = ces_aggregate(base_quality, accessibility, rho=0.5, axis=1)
    improved = ces_aggregate(better_quality, accessibility, rho=0.5, axis=1)
    assert improved[0] >= base[0]


def test_ces_empty_input_returns_zero_vector() -> None:
    quality = np.empty((0, 3))
    accessibility = np.empty((0, 3))
    result = ces_aggregate(quality, accessibility, rho=0.9, axis=0)
    assert result.shape == (3,)
    assert np.all(result == 0.0)


def test_ces_invalid_rho_raises() -> None:
    quality = np.array([[1.0, 0.5]])
    accessibility = np.array([[1.0, 1.0]])
    with pytest.raises(ValueError):
        ces_aggregate(quality, accessibility, rho=MAX_RHO + 1.0)


def test_ces_geometric_rho_matches_geometric_mean() -> None:
    quality = np.array([[1.0, 4.0]])
    accessibility = np.array([[0.5, 0.25]])
    product = quality * accessibility
    expected = np.exp(np.log(np.clip(product, 1e-12, None)).mean(axis=1))
    result = ces_aggregate(quality, accessibility, rho=0.0, axis=1)
    assert result[0] == pytest.approx(expected[0])


def test_ces_negative_rho_handles_inverse_emphasis() -> None:
    quality = np.array([[2.0, 0.5]])
    accessibility = np.array([[1.0, 2.0]])
    result = ces_aggregate(quality, accessibility, rho=-0.5, axis=1)
    assert result.shape == (1,)
    assert result[0] >= 0.0


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


ces_pair_strategy = st.lists(
    st.tuples(
        st.floats(0, 200, allow_nan=False, allow_infinity=False),
        st.floats(0, 50, allow_nan=False, allow_infinity=False),
    ),
    min_size=1,
    max_size=8,
)


@settings(deadline=None)
@given(ces_pair_strategy, st.floats(0.0, 1.0, allow_nan=False, allow_infinity=False))
def test_compute_z_monotonic_under_scaling(pairs: list[tuple[float, float]], rho: float) -> None:
    quality = np.array([pair[0] for pair in pairs], dtype=float)
    accessibility = np.array([pair[1] for pair in pairs], dtype=float)
    base = compute_z(quality, accessibility, rho)
    scaled = compute_z(quality * 1.5, accessibility, rho)
    assert np.all(base >= 0)
    assert np.all(scaled >= base - 1e-9)


@settings(deadline=None)
@given(ces_pair_strategy, st.floats(-0.9, 1.0, allow_nan=False, allow_infinity=False))
def test_ces_aggregate_monotonic(pairs: list[tuple[float, float]], rho: float) -> None:
    quality = np.array([pair[0] for pair in pairs], dtype=float)
    accessibility = np.array([pair[1] for pair in pairs], dtype=float)
    base = ces_aggregate(quality[np.newaxis, :], accessibility[np.newaxis, :], rho, axis=1)[0]
    scaled = ces_aggregate(
        (quality * 1.1)[np.newaxis, :], accessibility[np.newaxis, :], rho, axis=1
    )[0]
    assert scaled >= base - 1e-8


@settings(deadline=None)
@given(
    ces_pair_strategy,
    st.floats(-0.9, 1.0, allow_nan=False, allow_infinity=False),
    st.floats(0.1, 4.0),
)
def test_ces_homogeneous_in_quality(
    pairs: list[tuple[float, float]], rho: float, scale: float
) -> None:
    quality = np.array([pair[0] for pair in pairs], dtype=float)
    accessibility = np.array([pair[1] for pair in pairs], dtype=float)
    assume(np.all(quality > 0))
    assume(np.all(accessibility > 0))
    assume(abs(rho) > 1e-6)
    base = ces_aggregate(quality[np.newaxis, :], accessibility[np.newaxis, :], rho, axis=1)[0]
    max_float = np.finfo(np.float64).max
    assume(base < max_float / scale)
    scaled = ces_aggregate(
        (quality * scale)[np.newaxis, :], accessibility[np.newaxis, :], rho, axis=1
    )[0]
    expected = scale * base
    if expected >= max_float or scaled >= max_float:
        assert scaled == pytest.approx(max_float, rel=1e-6, abs=1e-6)
    else:
        assert pytest.approx(scaled, rel=1e-6, abs=1e-6) == expected


@settings(deadline=None)
@given(
    ces_pair_strategy,
    st.floats(-0.9, 1.0, allow_nan=False, allow_infinity=False),
    st.floats(0.1, 4.0),
)
def test_ces_homogeneous_in_accessibility(
    pairs: list[tuple[float, float]], rho: float, scale: float
) -> None:
    quality = np.array([pair[0] for pair in pairs], dtype=float)
    accessibility = np.array([pair[1] for pair in pairs], dtype=float)
    assume(np.all(accessibility > 0))
    assume(np.all(quality > 0))
    assume(abs(rho) > 1e-6)
    base = ces_aggregate(quality[np.newaxis, :], accessibility[np.newaxis, :], rho, axis=1)[0]
    max_float = np.finfo(np.float64).max
    assume(base < max_float / scale)
    scaled = ces_aggregate(
        quality[np.newaxis, :], (accessibility * scale)[np.newaxis, :], rho, axis=1
    )[0]
    expected = scale * base
    if expected >= max_float or scaled >= max_float:
        assert scaled == pytest.approx(max_float, rel=1e-6, abs=1e-6)
    else:
        assert pytest.approx(scaled, rel=1e-6, abs=1e-6) == expected


@settings(deadline=None)
@given(
    st.lists(st.floats(0, 200, allow_nan=False, allow_infinity=False), min_size=1, max_size=10),
    st.floats(0.01, 5.0, allow_nan=False, allow_infinity=False),
)
def test_apply_satiation_monotonic(values: list[float], kappa: float) -> None:
    sorted_values = np.sort(np.array(values, dtype=float))
    scores = apply_satiation(sorted_values, kappa)
    assert np.all((scores >= 0) & (scores <= 100))
    assert np.all(np.diff(scores) >= -1e-9)


@settings(deadline=None)
@given(
    st.integers(1, 4),
    st.integers(1, 4),
    st.data(),
)
def test_time_weighted_accessibility_matches_manual(rows: int, cols: int, data) -> None:
    utilities = data.draw(
        arrays(
            np.float64,
            shape=(rows, cols),
            elements=st.floats(-5, 5, allow_nan=False, allow_infinity=False),
        )
    )
    weights = data.draw(
        arrays(
            np.float64,
            shape=(cols,),
            elements=st.floats(0.1, 3.0, allow_nan=False, allow_infinity=False),
        )
    )
    result = time_weighted_accessibility(utilities, weights)
    manual = np.exp(utilities) @ weights
    assert np.allclose(result, manual)


@settings(deadline=None)
@given(
    st.integers(1, 4),
    st.integers(1, 4),
    st.floats(0.1, 3.0, allow_nan=False, allow_infinity=False),
    st.data(),
)
def test_nest_inclusive_monotonic(rows: int, cols: int, mu: float, data) -> None:
    utilities = data.draw(
        arrays(
            np.float64,
            shape=(rows, cols),
            elements=st.floats(-5, 5, allow_nan=False, allow_infinity=False),
        )
    )
    delta = data.draw(st.floats(0.1, 3.0, allow_nan=False, allow_infinity=False))
    base = nest_inclusive(utilities, mu)
    shifted = nest_inclusive(utilities + delta, mu)
    assert shifted.shape == (rows,)
    assert np.all(shifted >= base + delta - 1e-8)


@settings(deadline=None)
@given(
    st.integers(1, 4),
    st.integers(1, 4),
    st.floats(0.1, 3.0, allow_nan=False, allow_infinity=False),
    st.data(),
)
def test_nest_inclusive_bounds(rows: int, cols: int, mu: float, data) -> None:
    utilities = data.draw(
        arrays(
            np.float64,
            shape=(rows, cols),
            elements=st.floats(-5, 5, allow_nan=False, allow_infinity=False),
        )
    )
    values = nest_inclusive(utilities, mu)
    max_util = np.max(utilities, axis=1)
    min_util = np.min(utilities, axis=1)
    upper_bound = max_util + mu * np.log(cols)
    assert values.shape == (rows,)
    assert np.all(values >= min_util - 1e-8)
    assert np.all(values <= upper_bound + 1e-8)


@settings(deadline=None)
@given(
    st.integers(1, 4),
    st.floats(0.1, 3.0, allow_nan=False, allow_infinity=False),
    st.data(),
)
def test_top_level_logsum_monotonic(n_modes: int, mu_top: float, data) -> None:
    inclusive = data.draw(
        arrays(
            np.float64,
            shape=(1, n_modes),
            elements=st.floats(-4, 6, allow_nan=False, allow_infinity=False),
        )
    )
    bonus = data.draw(st.floats(0.1, 2.0, allow_nan=False, allow_infinity=False))
    base = top_level_logsum(inclusive, mu_top)
    improved = top_level_logsum(inclusive + bonus, mu_top)
    assert improved.shape == (1,)
    assert improved[0] >= base[0] + bonus - 1e-8


def test_mode_utility_returns_expected_types() -> None:
    params = ModeUtilityParams(beta0=1.5, alpha=0.4, comfort_weight=0.2)
    gtc = np.array([2.0, 3.0])
    comfort = np.array([0.5, 1.0])
    result = mode_utility(gtc, comfort, params)
    assert result.dtype == np.float64
    assert (
        pytest.approx(result[0])
        == params.beta0 - params.alpha * gtc[0] + params.comfort_weight * comfort[0]
    )
