import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from Urban_Amenities2.config.loader import load_params
from Urban_Amenities2.math.diversity import DiversityConfig
from Urban_Amenities2.scores.aggregation import (
    WeightConfig,
    aggregate_scores,
    compute_total_aucs,
)
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
            "quality": [90.0, 80.0],
            "brand": ["BrandA", "BrandB"],
            "name": ["A", "B"],
            "quality_components": [
                {"size": 85.0, "popularity": 90.0, "brand": 80.0, "heritage": 70.0},
                {"size": 70.0, "popularity": 60.0, "brand": 75.0, "heritage": 65.0},
            ],
            "brand_penalty": [1.0, 0.8],
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
    top = scores.loc[0, "contributors"]["grocery"][0]
    assert top["quality"] == pytest.approx(90.0)
    assert top["quality_components"]["popularity"] == pytest.approx(90.0)


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


def test_compute_total_aucs_uses_params_weights() -> None:
    subscores = pd.DataFrame(
        {
            "hex_id": ["h1", "h2"],
            "EA": [90.0, 40.0],
            "LCA": [80.0, 30.0],
            "MUHAA": [70.0, 20.0],
            "JEA": [60.0, 10.0],
            "MORR": [50.0, 5.0],
            "CTE": [40.0, 5.0],
            "SOU": [30.0, 5.0],
        }
    )
    params, _ = load_params("configs/params_default.yml")
    total = compute_total_aucs(subscores, params)
    assert {"hex_id", "aucs"} <= set(total.columns)
    assert total.loc[total["hex_id"] == "h1", "aucs"].iloc[0] > total.loc[total["hex_id"] == "h2", "aucs"].iloc[0]


@settings(deadline=None)
@given(
    st.lists(
        st.tuples(
            st.sampled_from(["hex1", "hex2", "hex3"]),
            st.sampled_from(["grocery", "health"]),
            st.floats(0, 100, allow_nan=False, allow_infinity=False),
            st.floats(0.1, 5.0, allow_nan=False, allow_infinity=False),
            st.floats(0.5, 1.0, allow_nan=False, allow_infinity=False),
        ),
        min_size=1,
        max_size=10,
    )
)
def test_essentials_access_property(records: list[tuple[str, str, float, float, float]]) -> None:
    pois_records = []
    access_records = []
    categories: set[str] = set()
    for idx, (hex_id, category, quality, weight, penalty) in enumerate(records):
        categories.add(category)
        poi_id = f"poi{idx}"
        pois_records.append(
            {
                "poi_id": poi_id,
                "aucstype": category,
                "quality": quality,
                "brand": category,
                "name": poi_id,
                "quality_components": {
                    "size": quality,
                    "popularity": quality,
                    "brand": quality,
                    "heritage": 0.0,
                },
                "brand_penalty": penalty,
            }
        )
        access_records.append({"hex_id": hex_id, "poi_id": poi_id, "weight": weight})

    pois = pd.DataFrame(pois_records)
    accessibility = pd.DataFrame(access_records)
    category_list = sorted(categories) or ["grocery"]
    config = EssentialsAccessConfig(
        categories=category_list,
        category_params=
        {
            category: EssentialCategoryConfig(rho=1.0, kappa=0.5, diversity=DiversityConfig())
            for category in category_list
        },
        top_k=3,
        shortfall_threshold=5.0,
        shortfall_penalty=1.0,
        shortfall_cap=10.0,
    )
    calculator = EssentialsAccessCalculator(config)
    scores, category_scores = calculator.compute(pois, accessibility)
    assert scores["EA"].between(0, 100).all()
    if not category_scores.empty:
        assert category_scores["score"].between(0, 100).all()
    for contributors in scores["contributors"].values:
        for items in contributors.values():
            contributions = [item["contribution"] for item in items]
            assert len(items) <= config.top_k
            assert contributions == sorted(contributions, reverse=True)
