import numpy as np
import pandas as pd
import pytest

from Urban_Amenities2.quality import (
    BrandDedupeConfig,
    QualityScorer,
    QualityScoringConfig,
    apply_brand_dedupe,
    summarize_quality,
)


def _scoring_config() -> QualityScoringConfig:
    return QualityScoringConfig(
        component_weights={"size": 0.3, "popularity": 0.4, "brand": 0.15, "heritage": 0.15},
        z_clip_abs=3.0,
        opening_hours_bonus_xi=1.0,
        category_defaults={"grocery": {"size": 2.0, "popularity": 1.0, "brand": 0.5, "heritage": 0.1}},
        hours_defaults={"grocery": "standard", "cafe": "extended"},
    )


def test_quality_components_rank() -> None:
    pois = pd.DataFrame(
        {
            "poi_id": ["a", "b", "c"],
            "aucstype": ["grocery", "grocery", "grocery"],
            "square_footage": [1000, 5000, np.nan],
            "seating_capacity": [np.nan, np.nan, 120],
            "median_views": [50, 5000, 120],
            "brand": ["Local", "National", "Coop"],
            "brand_wd": [None, "Q1", None],
            "heritage_status": [None, None, "UNESCO"],
            "hours_per_day": [8, 16, np.nan],
        }
    )
    scorer = QualityScorer(_scoring_config())
    scored = scorer.score(pois)
    assert scored["quality"].between(0, 100).all()
    assert scored.loc[1, "quality"] > scored.loc[0, "quality"]
    assert scored.loc[2, "quality"] > scored.loc[0, "quality"]
    assert scored.loc[2, "quality_hours_category"] == "standard"
    summary = summarize_quality(scored)
    assert summary.loc[0, "count"] == len(pois)


def test_quality_property_range() -> None:
    rng = np.random.default_rng(42)
    pois = pd.DataFrame(
        {
            "poi_id": [f"p{i}" for i in range(50)],
            "aucstype": rng.choice(["grocery", "cafe"], size=50),
            "square_footage": rng.integers(100, 10_000, size=50),
            "median_views": rng.integers(0, 10_000, size=50),
            "brand": rng.choice(["Local", "Chain"], size=50),
            "hours_per_day": rng.integers(4, 24, size=50),
        }
    )
    scorer = QualityScorer(_scoring_config())
    scored = scorer.score(pois)
    assert scored["quality"].between(0, 100).all()
    assert not scored["quality"].isna().any()


def test_quality_summary_comparison() -> None:
    pois = pd.DataFrame(
        {
            "poi_id": ["g1", "g2", "c1", "c2"],
            "aucstype": ["grocery", "grocery", "cafe", "cafe"],
            "square_footage": [2000, 1500, 400, 600],
            "median_views": [200, 150, 800, 900],
            "brand": ["Market", "Market", "Cafe", "Cafe"],
            "hours_per_day": [12, 10, 18, 24],
        }
    )
    scorer = QualityScorer(_scoring_config())
    scored = scorer.score(pois)
    summary = summarize_quality(scored)
    assert set(summary["aucstype"]) == {"grocery", "cafe"}
    grocery_mean = summary.set_index("aucstype").loc["grocery", "mean_quality"]
    cafe_mean = summary.set_index("aucstype").loc["cafe", "mean_quality"]
    assert grocery_mean != cafe_mean


def test_opening_hours_bonus() -> None:
    pois = pd.DataFrame(
        {
            "poi_id": ["x", "y"],
            "aucstype": ["cafe", "cafe"],
            "square_footage": [500, 500],
            "median_views": [100, 100],
            "brand": ["Cafe", "Cafe"],
            "opening_hours": ["Mo-Su 07:00-19:00", "24/7"],
        }
    )
    scorer = QualityScorer(_scoring_config())
    scored = scorer.score(pois)
    assert scored.loc[1, "quality"] > scored.loc[0, "quality"]
    assert scored.loc[1, "quality_hours_category"] == "24_7"


def test_brand_dedupe_preserves_weight() -> None:
    pois = pd.DataFrame(
        {
            "poi_id": ["a", "b"],
            "aucstype": ["grocery", "grocery"],
            "brand": ["Chain", "Chain"],
            "lat": [40.0, 40.001],
            "lon": [-105.0, -105.001],
            "quality": [80.0, 60.0],
        }
    )
    config = BrandDedupeConfig(distance_threshold_m=500, beta_per_km=2.0)
    deduped, stats = apply_brand_dedupe(pois, config)
    assert pytest.approx(deduped["brand_weight"].sum()) == pytest.approx(pois["quality"].sum())
    assert stats["affected_ratio"] > 0
    assert deduped.loc[deduped["poi_id"] == "b", "brand_penalty"].iloc[0] < 1.0
