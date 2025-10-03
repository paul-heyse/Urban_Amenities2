"""Extended coverage for `Urban_Amenities2.math.satiation`."""

from __future__ import annotations

import math

import numpy as np
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st
from tests.fixtures.math_samples import SATIATION_REGRESSION_VECTORS
from tests.math.strategies import amenity_counts, satiation_lambdas

from Urban_Amenities2.math.satiation import (
    apply_satiation,
    compute_kappa_from_anchor,
    resolve_kappa,
    satiation_weight,
)


def test_satiation_weight_matches_closed_form() -> None:
    n = 4
    lam = 0.75
    expected = (1.0 - math.exp(-lam * n)) / n
    result = satiation_weight(float(n), float(lam))
    assert result.shape == ()
    assert float(result) == pytest.approx(expected, rel=1e-12, abs=1e-12)


@pytest.mark.parametrize("n, lam, expected, rtol, atol", SATIATION_REGRESSION_VECTORS)
def test_satiation_weight_regressions(
    n: int, lam: float, expected: float, rtol: float, atol: float
) -> None:
    result = float(satiation_weight(float(n), lam))
    assert result == pytest.approx(expected, rel=rtol, abs=atol)


def test_satiation_lambda_sensitivity() -> None:
    n = 10
    weak = float(satiation_weight(n, 0.1))
    medium = float(satiation_weight(n, 1.0))
    strong = float(satiation_weight(n, 5.0))
    assert weak < medium <= strong
    assert weak == pytest.approx((1.0 - math.exp(-1.0)) / n, rel=1e-6)
    assert strong <= 0.1


def test_satiation_weight_raises_for_zero_or_negative_counts() -> None:
    with pytest.raises(ValueError, match="n must be positive"):
        satiation_weight(0.0, 0.5)
    with pytest.raises(ValueError, match="n must be positive"):
        satiation_weight(np.array([1.0, 0.0]), 0.5)
    with pytest.raises(ValueError):
        satiation_weight(-3.0, 0.5)


def test_satiation_weight_raises_for_non_positive_lambda() -> None:
    with pytest.raises(ValueError, match="lambda must be positive"):
        satiation_weight(1.0, 0.0)


def test_satiation_weight_vectorised() -> None:
    counts = np.array([1, 2, 5, 10], dtype=float)
    lam = 0.75
    weights = satiation_weight(counts, lam)
    manual = np.array([(1.0 - math.exp(-lam * c)) / c for c in counts], dtype=float)
    assert np.allclose(weights, manual, rtol=1e-12, atol=1e-12)


def test_satiation_weight_large_n_asymptote() -> None:
    lam = 1.0
    weight = float(satiation_weight(1_000_000.0, lam))
    assert weight < 1e-5


@settings(deadline=None, max_examples=120)
@given(
    st.builds(
        lambda a, b: (a, b),
        amenity_counts,
        amenity_counts,
    ),
    satiation_lambdas,
)
def test_satiation_monotonicity(pair: tuple[int, int], lam: float) -> None:
    n1, n2 = pair
    assume(n1 < n2)
    w1 = float(satiation_weight(n1, lam))
    w2 = float(satiation_weight(n2, lam))
    assert w1 > w2


def test_apply_satiation_aligns_with_weights() -> None:
    values = np.array([1.0, 2.0, 5.0, 10.0], dtype=float)
    lam = 0.3
    scores = apply_satiation(values, lam)
    weights = satiation_weight(values, lam)
    expected_scores = 100.0 * (1.0 - np.exp(-lam * values))
    assert np.allclose(scores, expected_scores)
    assert np.allclose(weights, expected_scores / (100.0 * values), rtol=1e-9, atol=1e-9)


def test_apply_satiation_rejects_non_positive_kappa() -> None:
    with pytest.raises(ValueError, match="kappa must be positive"):
        apply_satiation(np.array([1.0]), 0.0)
    with pytest.raises(ValueError, match="kappa must be positive"):
        apply_satiation(np.array([1.0]), np.array([-0.1]))


def test_apply_satiation_caps_output_at_hundred() -> None:
    values = np.array([10.0], dtype=float)
    kappa = np.array([10.0], dtype=float)
    result = apply_satiation(values, kappa)
    assert result.shape == (1,)
    assert result[0] == 100.0


def test_satiation_mixed_array_raises_for_invalid_entry() -> None:
    counts = np.array([1.0, -1.0, 5.0])
    with pytest.raises(ValueError):
        satiation_weight(counts, 0.5)


def test_compute_kappa_from_anchor_validation() -> None:
    with pytest.raises(ValueError, match="target_value must be positive"):
        compute_kappa_from_anchor(50.0, 0.0)
    with pytest.raises(ValueError, match="target_score must be between 0 and 100"):
        compute_kappa_from_anchor(0.0, 1.0)


def test_resolve_kappa_handles_dict_and_anchors() -> None:
    kappa = {"a": 0.5}
    anchors = {"b": (50.0, 2.0)}
    resolved = resolve_kappa(kappa, anchors)
    assert resolved["a"] == 0.5
    assert resolved["b"] == pytest.approx(compute_kappa_from_anchor(50.0, 2.0))


def test_resolve_kappa_scalar_maps_to_default_key() -> None:
    resolved = resolve_kappa(0.75)
    assert resolved == {"default": 0.75}


def test_resolve_kappa_rejects_invalid_inputs() -> None:
    with pytest.raises(ValueError, match="kappa values must be positive"):
        resolve_kappa({"a": -0.1})
    with pytest.raises(ValueError, match="kappa must be positive"):
        resolve_kappa(-1.0)
    with pytest.raises(TypeError):
        resolve_kappa("invalid")
