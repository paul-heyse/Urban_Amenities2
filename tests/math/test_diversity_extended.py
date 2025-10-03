"""Extended coverage for `Urban_Amenities2.math.diversity`."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings

from Urban_Amenities2.math.diversity import (
    DiversityConfig,
    compute_diversity,
    diversity_multiplier,
    shannon_entropy,
)
from tests.fixtures.math_samples import DIVERSITY_REGRESSION_VECTORS
from tests.math.strategies import diversity_counts


def test_uniform_distribution_maximises_entropy() -> None:
    counts = [10.0, 10.0, 10.0, 10.0]
    entropy = shannon_entropy(counts)
    assert entropy == pytest.approx(math.log(len(counts)), rel=1e-12)
    multiplier = diversity_multiplier(counts)
    assert multiplier == pytest.approx(1.2, rel=1e-9)


def test_skewed_distribution_reduces_diversity() -> None:
    uniform = [25.0, 25.0, 25.0, 25.0]
    skewed = [100.0, 1.0, 1.0, 1.0]
    assert diversity_multiplier(skewed) < diversity_multiplier(uniform)


def test_single_category_has_no_diversity() -> None:
    counts = [50.0]
    multiplier = diversity_multiplier(counts)
    assert multiplier == pytest.approx(1.0, rel=1e-12)
    assert shannon_entropy(counts) == 0.0


def test_zero_count_categories_are_ignored() -> None:
    frame = pd.DataFrame(
        {
            "hex_id": ["h1", "h1", "h1", "h1"],
            "category": ["grocery"] * 4,
            "subtype": ["a", "b", "c", "d"],
            "qw": [10.0, 0.0, 0.0, 5.0],
        }
    )
    result = compute_diversity(frame, "qw", ["hex_id", "category"], "subtype")
    row = result.iloc[0]
    expected = diversity_multiplier([10.0, 5.0])
    assert row["diversity_multiplier"] == pytest.approx(expected, rel=1e-9)


@pytest.mark.parametrize("counts, expected", DIVERSITY_REGRESSION_VECTORS)
def test_shannon_entropy_regressions(counts: list[float], expected: float) -> None:
    assert shannon_entropy(counts) == pytest.approx(expected, rel=1e-9)


@settings(deadline=None, max_examples=100)
@given(diversity_counts)
def test_diversity_increases_with_even_distribution(counts: list[float]) -> None:
    array = np.asarray(counts, dtype=float)
    mean_value = array.mean()
    even = np.full_like(array, mean_value)
    baseline = diversity_multiplier(array)
    even_multiplier = diversity_multiplier(even)
    assert even_multiplier >= baseline - 1e-9


def test_diversity_config_cap_respected() -> None:
    counts = [10.0, 10.0, 10.0]
    config = DiversityConfig(weight=0.5, min_multiplier=1.0, max_multiplier=1.1, cap=0.05)
    multiplier = diversity_multiplier(counts, config)
    assert multiplier <= config.min_multiplier + config.cap


def test_simpson_index_matches_manual_value() -> None:
    counts = np.array([8.0, 4.0, 2.0], dtype=float)
    probabilities = counts / counts.sum()
    simpson = 1.0 - np.sum(probabilities**2)
    assert simpson == pytest.approx(0.5714285714285714, rel=1e-12)


def test_all_zero_counts_return_baseline_multiplier() -> None:
    counts = [0.0, 0.0, 0.0]
    assert shannon_entropy(counts) == 0.0
    assert diversity_multiplier(counts) == pytest.approx(1.0, rel=1e-12)


def test_compute_diversity_missing_columns_raise() -> None:
    frame = pd.DataFrame({"hex_id": ["h1"], "subtype": ["a"], "qw": [1.0]})
    with pytest.raises(KeyError):
        compute_diversity(frame, "missing", ["hex_id"], "subtype")
    with pytest.raises(KeyError):
        compute_diversity(frame, "qw", ["hex_id"], "missing")


def test_shannon_entropy_ignores_negative_values() -> None:
    counts = [10.0, -5.0, 5.0]
    baseline = shannon_entropy([10.0, 5.0])
    assert shannon_entropy(counts) == pytest.approx(baseline, rel=1e-12)


def test_diversity_multiplier_clamps_to_minimum() -> None:
    counts = [0.1]
    config = DiversityConfig(weight=5.0, min_multiplier=0.8, max_multiplier=2.0)
    assert diversity_multiplier(counts, config) == pytest.approx(config.min_multiplier, rel=1e-12)


def test_diversity_config_validates_inputs() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        DiversityConfig(weight=-0.1)
    with pytest.raises(ValueError, match="min_multiplier must be positive"):
        DiversityConfig(min_multiplier=0.0)
    with pytest.raises(ValueError, match=">= min_multiplier"):
        DiversityConfig(min_multiplier=1.0, max_multiplier=0.5)
    with pytest.raises(ValueError, match="cap must be non-negative"):
        DiversityConfig(cap=-0.5)
