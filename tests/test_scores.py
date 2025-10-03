import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pandas.testing import assert_frame_equal

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


@pytest.fixture()
def essentials_inputs() -> tuple[pd.DataFrame, pd.DataFrame, EssentialsAccessConfig]:
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
            "brand_penalty": [1.0, 1.0],
        }
    )
    accessibility = pd.DataFrame(
        {
            "origin_hex": ["hex1", "hex1", "hex2"],
            "poi_id": ["p1", "p2", "p2"],
            "mode": ["car", "car", "car"],
            "period": ["AM", "AM", "AM"],
            "weight": [1.0, 0.5, 0.4],
        }
    )
    config = EssentialsAccessConfig(
        categories=["grocery"],
        category_params={
            "grocery": EssentialCategoryConfig(
                rho=1.0,
                kappa=0.05,
                diversity=DiversityConfig(weight=0.0, min_multiplier=1.0, max_multiplier=1.0),
            )
        },
        shortfall_threshold=95.0,
        shortfall_penalty=2.0,
        shortfall_cap=4.0,
        top_k=3,
    )
    return pois, accessibility, config


@pytest.fixture()
def normalization_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "region": ["A", "A", "B"],
            "score": [50.0, 80.0, 40.0],
            "ea": [60.0, 70.0, 50.0],
            "health": [40.0, 90.0, 70.0],
        }
    )


@pytest.fixture()
def aggregation_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "hex_id": ["h1", "h2"],
            "ea": [90.0, 40.0],
            "health": [80.0, 30.0],
        }
    )


def test_essentials_access_deterministic(essentials_inputs: tuple[pd.DataFrame, pd.DataFrame, EssentialsAccessConfig]) -> None:
    pois, accessibility, config = essentials_inputs
    calculator = EssentialsAccessCalculator(config)
    scores, category_scores = calculator.compute(pois.copy(), accessibility.copy())

    actual_scores = scores.sort_values("hex_id").reset_index(drop=True)
    expected_scores = pd.DataFrame(
        {
            "hex_id": ["hex1", "hex2"],
            "EA": [99.84965608070225, 77.81034820053446],
            "penalty": [0.0, 2.0],
        }
    )
    assert_frame_equal(
        actual_scores[["hex_id", "EA", "penalty"]],
        expected_scores,
        rtol=1e-6,
        atol=1e-8,
        check_like=True,
    )

    actual_category = category_scores.sort_values(["hex_id", "category"]).reset_index(drop=True)
    expected_category = pd.DataFrame(
        {
            "hex_id": ["hex1", "hex2"],
            "category": ["grocery", "grocery"],
            "V": [130.0, 32.0],
            "satiation": [99.84965608070225, 79.81034820053446],
            "diversity_multiplier": [1.0, 1.0],
            "entropy": [0.6172417697303416, 0.0],
            "score": [99.84965608070225, 79.81034820053446],
        }
    )
    assert_frame_equal(
        actual_category[[
            "hex_id",
            "category",
            "V",
            "satiation",
            "diversity_multiplier",
            "entropy",
            "score",
        ]],
        expected_category,
        rtol=1e-6,
        atol=1e-8,
        check_like=True,
    )

    grocery_scores = actual_scores.set_index("hex_id")["category_scores"]
    assert grocery_scores["hex1"]["grocery"] == pytest.approx(99.84965608070225)
    assert grocery_scores["hex2"]["grocery"] == pytest.approx(79.81034820053446)

    contributors = actual_scores.set_index("hex_id")["contributors"]["hex1"]["grocery"]
    contributions = [entry["contribution"] for entry in contributors]
    assert contributions == sorted(contributions, reverse=True)
    assert contributions[0] == pytest.approx(90.0)
    assert contributions[1] == pytest.approx(40.0)


def test_essentials_access_handles_non_numeric_inputs(
    essentials_inputs: tuple[pd.DataFrame, pd.DataFrame, EssentialsAccessConfig]
) -> None:
    pois, accessibility, config = essentials_inputs
    pois_with_strings = pois.copy()
    accessibility_with_strings = accessibility.copy()
    accessibility_with_strings["weight"] = accessibility_with_strings["weight"].astype(str)

    calculator = EssentialsAccessCalculator(config)
    scores, category_scores = calculator.compute(pois_with_strings, accessibility_with_strings)

    assert scores["EA"].between(0, 100).all()
    assert scores["penalty"].ge(0).all()
    assert category_scores["score"].between(0, 100).all()


def test_normalization_and_aggregation_snapshots(
    normalization_frame: pd.DataFrame, aggregation_frame: pd.DataFrame
) -> None:
    percentile = normalize_scores(
        normalization_frame.copy(),
        "region",
        "score",
        NormalizationConfig(mode="percentile"),
    )
    expected_percentile = normalization_frame.copy()
    expected_percentile["score_normalized"] = [0.0, 100.0, 0.0]
    assert_frame_equal(
        percentile.sort_values(["region", "score"]).reset_index(drop=True),
        expected_percentile.sort_values(["region", "score"]).reset_index(drop=True),
        check_like=True,
        atol=1e-8,
    )

    standard = normalize_scores(
        normalization_frame.copy(),
        "region",
        "score",
        NormalizationConfig(mode="standard", standard_target=80.0),
    )
    expected_standard = normalization_frame.copy()
    expected_standard["score_normalized"] = [62.5, 100.0, 50.0]
    assert_frame_equal(
        standard.sort_values(["region", "score"]).reset_index(drop=True),
        expected_standard.sort_values(["region", "score"]).reset_index(drop=True),
        check_like=True,
        atol=1e-8,
    )

    weights = WeightConfig({"ea": 0.6, "health": 0.4})
    aggregated = aggregate_scores(aggregation_frame.copy(), "composite", weights)
    expected_aggregated = aggregation_frame.copy()
    expected_aggregated["composite"] = [0.6 * 90.0 + 0.4 * 80.0, 0.6 * 40.0 + 0.4 * 30.0]
    assert_frame_equal(
        aggregated.sort_values("hex_id").reset_index(drop=True),
        expected_aggregated.sort_values("hex_id").reset_index(drop=True),
        check_like=True,
        atol=1e-8,
    )


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
    weights = {
        "EA": 40.0,
        "LCA": 20.0,
        "MUHAA": 10.0,
        "JEA": 10.0,
        "MORR": 10.0,
        "CTE": 5.0,
        "SOU": 5.0,
    }

    class _StubSubscores:
        def __init__(self, mapping: dict[str, float]):
            self._mapping = mapping

        def model_dump(self) -> dict[str, float]:
            return dict(self._mapping)

    class _StubParams:
        def __init__(self, mapping: dict[str, float]):
            self.subscores = _StubSubscores(mapping)

    params = _StubParams(weights)
    total = compute_total_aucs(subscores, params)  # type: ignore[arg-type]
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
