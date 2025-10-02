import pandas as pd
import pytest

from Urban_Amenities2.math.diversity import DiversityConfig
from Urban_Amenities2.scores.aggregation import WeightConfig, aggregate_scores
from Urban_Amenities2.scores.essentials_access import (
    EssentialCategoryConfig,
    EssentialsAccessCalculator,
    EssentialsAccessConfig,
)
from Urban_Amenities2.scores.normalization import NormalizationConfig, normalize_scores


def test_essentials_access_calculation() -> None:
    pois = pd.DataFrame(
        {
            "poi_id": ["p1", "p2"],
            "aucstype": ["grocery", "grocery"],
            "quality": [0.9, 0.8],
            "brand": ["BrandA", "BrandB"],
            "name": ["A", "B"],
        }
    )
    accessibility = pd.DataFrame(
        {
            "origin_hex": ["hex1", "hex1"],
            "poi_id": ["p1", "p2"],
            "mode": ["car", "car"],
            "period": ["AM", "AM"],
            "weight": [1.0, 0.5],
        }
    )

    config = EssentialsAccessConfig(
        categories=["grocery"],
        category_params={
            "grocery": EssentialCategoryConfig(
                rho=1.0,
                kappa=0.5,
                diversity=DiversityConfig(weight=1.0, cap=2.0),
            )
        },
        shortfall_threshold=10.0,
        shortfall_penalty=1.0,
        shortfall_cap=5.0,
        top_k=2,
    )

    calculator = EssentialsAccessCalculator(config)
    scores, category_scores = calculator.compute(pois, accessibility)
    assert {"hex_id", "EA", "penalty", "category_scores", "contributors"} <= set(scores.columns)
    assert not category_scores.empty
    assert scores.loc[0, "EA"] >= 0


def test_normalization_and_aggregation() -> None:
    frame = pd.DataFrame(
        {
            "region": ["A", "A", "B"],
            "score": [50, 80, 40],
            "ea": [60, 70, 50],
            "health": [40, 90, 70],
        }
    )

    percentile = normalize_scores(frame, "region", "score", NormalizationConfig(mode="percentile"))
    assert percentile["score_normalized"].between(0, 100).all()

    standard = normalize_scores(frame.copy(), "region", "score", NormalizationConfig(mode="standard", standard_target=80))
    assert standard["score_normalized"].max() <= 100

    weights = WeightConfig({"ea": 0.6, "health": 0.4})
    aggregated = aggregate_scores(frame.copy(), "composite", weights)
    assert aggregated.loc[0, "composite"] == pytest.approx(0.6 * 60 + 0.4 * 40)
