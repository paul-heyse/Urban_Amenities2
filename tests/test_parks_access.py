import pandas as pd

from Urban_Amenities2.scores.parks_access import (
    ParkQualityConfig,
    ParkQualityWeights,
    ParksTrailsAccessCalculator,
    ParksTrailsAccessConfig,
)


def test_quality_computation_uses_components() -> None:
    config = ParkQualityConfig(
        area_range=(2.0, 100.0),
        amenities_range=(0.0, 10.0),
        designation_weights={"national_park": 1.0, "city_park": 0.5},
        weights=ParkQualityWeights(area=0.5, amenities=0.3, designation=0.2),
    )
    parks = pd.DataFrame(
        {
            "poi_id": ["p1", "p2"],
            "area_acres": [5.0, 80.0],
            "amenities": [2, 8],
            "designation": ["city_park", "national_park"],
        }
    )
    calc = ParksTrailsAccessCalculator(ParksTrailsAccessConfig(quality=config))
    table = calc._quality_table(parks)
    assert table["quality_score"].iloc[1] > table["quality_score"].iloc[0]
    assert table["quality_score"].between(0, 100).all()


def test_parks_accessibility_scores_hexes() -> None:
    parks = pd.DataFrame(
        {
            "poi_id": ["p1", "p2"],
            "area_acres": [50.0, 10.0],
            "amenities": [5, 1],
            "designation": ["national_park", "city_park"],
        }
    )
    accessibility = pd.DataFrame(
        {
            "origin_hex": ["a", "a", "b"],
            "poi_id": ["p1", "p2", "p2"],
            "weight": [0.8, 0.2, 0.5],
        }
    )
    calculator = ParksTrailsAccessCalculator()
    scores = calculator.compute(parks, accessibility)
    assert set(scores.columns) == {"hex_id", "parks_score"}
    high = scores.loc[scores["hex_id"] == "a", "parks_score"].iloc[0]
    low = scores.loc[scores["hex_id"] == "b", "parks_score"].iloc[0]
    assert high > low
    assert scores["parks_score"].between(0, 100).all()


def test_parks_accessibility_returns_zero_when_missing() -> None:
    parks = pd.DataFrame(
        {"poi_id": ["p1"], "area_acres": [5.0], "amenities": [2], "designation": ["city_park"]}
    )
    accessibility = pd.DataFrame({"origin_hex": ["z"], "poi_id": ["unknown"], "weight": [0.5]})
    calculator = ParksTrailsAccessCalculator()
    scores = calculator.compute(parks, accessibility)
    assert scores.empty
