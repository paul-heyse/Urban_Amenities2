import pandas as pd
import pytest

from Urban_Amenities2.config.loader import load_params
from Urban_Amenities2.scores.leisure_culture_access import (
    LeisureCultureAccessCalculator,
    LeisureCultureAccessConfig,
    compute_novelty_table,
    compute_pageview_volatility,
)


def test_pageview_volatility_computation() -> None:
    volatility, mean = compute_pageview_volatility([100, 140, 80, 160])
    assert mean == pytest.approx(120.0)
    assert volatility > 0


def test_compute_novelty_table_applies_bonus() -> None:
    config = LeisureCultureAccessConfig()
    novelty = pd.DataFrame(
        {
            "poi_id": ["p1", "p2"],
            config.novelty.views_column: [[150, 200, 100], [5, 6, 4]],
        }
    )
    table = compute_novelty_table(novelty, config.novelty)
    multiplier_col = config.novelty.multiplier_column
    assert table.loc[0, multiplier_col] > 1.0
    assert table.loc[1, multiplier_col] == pytest.approx(1.0)


def test_leisure_culture_access_computation() -> None:
    pois = pd.DataFrame(
        {
            "poi_id": ["p1", "p2", "p3"],
            "category": ["restaurants", "museums_galleries", "restaurants"],
            "quality": [80.0, 90.0, 70.0],
        }
    )
    accessibility = pd.DataFrame(
        {
            "hex_id": ["h1", "h1", "h2"],
            "poi_id": ["p1", "p2", "p3"],
            "weight": [0.6, 0.4, 1.0],
        }
    )
    novelty = pd.DataFrame(
        {
            "poi_id": ["p1", "p2", "p3"],
            "daily_views": [[100, 120, 110], [200, 210, 220], [10, 12, 9]],
        }
    )
    params, _ = load_params("configs/params_default.yml")
    calculator = LeisureCultureAccessCalculator.from_params(params)
    summary, category_scores = calculator.compute(pois, accessibility, novelty=novelty)
    assert {"hex_id", "LCA", "category_scores"} <= set(summary.columns)
    assert summary["LCA"].between(0, 100).all()
    assert not category_scores.empty
    assert category_scores["score"].between(0, 100).all()
    high_hex = summary.loc[summary["hex_id"] == "h1", "LCA"].iloc[0]
    low_hex = summary.loc[summary["hex_id"] == "h2", "LCA"].iloc[0]
    assert high_hex >= low_hex
