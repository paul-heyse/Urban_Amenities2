import numpy as np
import pandas as pd

from Urban_Amenities2.dedupe.pois import DedupeConfig, deduplicate_pois
from Urban_Amenities2.math.ces import ces_aggregate
from Urban_Amenities2.quality.dedupe import BrandDedupeConfig, apply_brand_dedupe


def test_ces_aggregate_matches_expected_behaviour() -> None:
    quality = np.array([[1.0, 2.0], [0.5, 1.5]], dtype=float)
    accessibility = np.array([[0.8, 0.2], [1.0, 0.5]], dtype=float)
    linear = ces_aggregate(quality, accessibility, rho=1.0, axis=1)
    assert np.allclose(linear, np.sum(quality * accessibility, axis=1))
    geometric = ces_aggregate(quality, accessibility, rho=0.0, axis=1)
    manual_geo = np.exp(np.log(np.maximum(quality * accessibility, 1e-12)).mean(axis=1))
    assert np.allclose(geometric, manual_geo)
    rho = 0.5
    ces = ces_aggregate(quality, accessibility, rho=rho, axis=1)
    assert np.all(ces >= 0)


def test_brand_dedupe_penalises_close_stores() -> None:
    pois = pd.DataFrame(
        {
            "poi_id": ["a", "b"],
            "brand": ["Chain", "Chain"],
            "aucstype": ["grocery", "grocery"],
            "lat": [39.0, 39.0002],
            "lon": [-104.0, -104.0002],
            "quality": [80.0, 70.0],
        }
    )
    config = BrandDedupeConfig(distance_threshold_m=50.0, beta_per_km=1.0)
    deduped, stats = apply_brand_dedupe(pois, config)
    assert {"brand_penalty", "brand_weight"} <= set(deduped.columns)
    assert stats["affected_ratio"] > 0
    assert deduped["brand_penalty"].between(0.0, 1.0).all()


def test_deduplicate_pois_removes_nearby_duplicates() -> None:
    frame = pd.DataFrame(
        {
            "poi_id": ["p1", "p2", "p3"],
            "hex_id": ["h1", "h1", "h2"],
            "brand": ["Chain", "Chain", "Solo"],
            "name": ["Chain One", "Chain Two", "Solo"],
            "lat": [39.0, 39.0001, 39.1],
            "lon": [-104.0, -104.0001, -104.2],
            "aucstype": ["grocery", "grocery", "grocery"],
            "confidence": [0.9, 0.8, 0.95],
        }
    )
    config = DedupeConfig()
    result = deduplicate_pois(frame, config=config)
    remaining = set(result["poi_id"])
    assert remaining == {"p1", "p3"}
    assert "dedupe_weight" in result.columns
    weight_p1 = float(result.loc[result["poi_id"] == "p1", "dedupe_weight"].iloc[0])
    assert weight_p1 <= 1.0
