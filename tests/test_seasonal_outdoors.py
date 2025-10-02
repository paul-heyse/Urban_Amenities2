import pandas as pd

from Urban_Amenities2.scores.seasonal_outdoors import (
    ClimateComfortConfig,
    SeasonalOutdoorsCalculator,
    SeasonalOutdoorsConfig,
    compute_monthly_comfort,
)


def _monthly_frame(value: float) -> dict[str, float]:
    return {f"temp_{month}": value for month in ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")}


def _zero_precip() -> dict[str, float]:
    return {f"precip_{month}": 0.1 for month in ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")}


def _calm_wind() -> dict[str, float]:
    return {f"wind_{month}": 10.0 for month in ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")}


def test_compute_monthly_comfort_within_range() -> None:
    config = ClimateComfortConfig()
    score = compute_monthly_comfort(temperature=70.0, precipitation=0.2, wind=10.0, config=config)
    assert 0.99 <= score <= 1.0


def test_sou_scores_respect_climate_adjustment() -> None:
    parks = pd.DataFrame({"hex_id": ["a", "b"], "parks_score": [80.0, 80.0]})
    pleasant = {**_monthly_frame(70.0), **_zero_precip(), **_calm_wind()}
    harsh = {**_monthly_frame(95.0), **_zero_precip(), **_calm_wind()}
    climate = pd.DataFrame(
        [
            {"hex_id": "a", **pleasant},
            {"hex_id": "b", **harsh},
        ]
    )
    calculator = SeasonalOutdoorsCalculator(SeasonalOutdoorsConfig())
    results = calculator.compute(parks, climate)
    pleasant_score = results.loc[results["hex_id"] == "a", "SOU"].iloc[0]
    harsh_score = results.loc[results["hex_id"] == "b", "SOU"].iloc[0]
    assert pleasant_score > harsh_score
    assert 0 <= harsh_score <= pleasant_score <= 80


def test_zero_parks_score_results_in_zero_sou() -> None:
    parks = pd.DataFrame({"hex_id": ["c"], "parks_score": [0.0]})
    climate = pd.DataFrame({"hex_id": ["c"], **_monthly_frame(70.0), **_zero_precip(), **_calm_wind()})
    calculator = SeasonalOutdoorsCalculator()
    results = calculator.compute(parks, climate)
    assert results.loc[0, "SOU"] == 0
