import numpy as np
import pandas as pd
import pytest

from Urban_Amenities2.scores.seasonal_outdoors import (
    ClimateComfortConfig,
    SeasonalOutdoorsCalculator,
    SeasonalOutdoorsConfig,
    compute_monthly_comfort,
    compute_sigma_out,
    extract_parks_score,
)


def _all_months() -> tuple[str, ...]:
    return (
        "jan",
        "feb",
        "mar",
        "apr",
        "may",
        "jun",
        "jul",
        "aug",
        "sep",
        "oct",
        "nov",
        "dec",
    )


def _monthly_frame(value: float) -> dict[str, float]:
    return {f"temp_{month}": value for month in _all_months()}


def _zero_precip() -> dict[str, float]:
    return {f"precip_{month}": 0.1 for month in _all_months()}


def _calm_wind() -> dict[str, float]:
    return {f"wind_{month}": 10.0 for month in _all_months()}


def test_compute_monthly_comfort_within_range() -> None:
    config = ClimateComfortConfig()
    score = compute_monthly_comfort(temperature=70.0, precipitation=0.2, wind=10.0, config=config)
    assert 0.99 <= score <= 1.0


def test_compute_monthly_comfort_is_bounded_randomized() -> None:
    rng = np.random.default_rng(123)
    config = ClimateComfortConfig()
    for _ in range(50):
        temperature = float(rng.uniform(-40.0, 120.0))
        precipitation = float(rng.uniform(0.0, 3.0))
        wind = float(rng.uniform(0.0, 60.0))
        score = compute_monthly_comfort(
            temperature=temperature,
            precipitation=precipitation,
            wind=wind,
            config=config,
        )
        assert 0.0 <= score <= 1.0


def test_compute_sigma_out_is_bounded_randomized() -> None:
    rng = np.random.default_rng(321)
    config = ClimateComfortConfig()
    for _ in range(25):
        temps = rng.uniform(-20.0, 120.0, size=12)
        precips = rng.uniform(0.0, 3.0, size=12)
        winds = rng.uniform(0.0, 60.0, size=12)
        data = {}
        for month, temp, precip, wind in zip(_all_months(), temps, precips, winds, strict=False):
            data[f"temp_{month}"] = float(temp)
            data[f"precip_{month}"] = float(precip)
            data[f"wind_{month}"] = float(wind)
        row = pd.Series(data)
        sigma = compute_sigma_out(row, config)
        assert 0.0 <= sigma <= 1.0


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
    assert results["sigma_out"].between(0, 1).all()


def test_zero_parks_score_results_in_zero_sou() -> None:
    parks = pd.DataFrame({"hex_id": ["c"], "parks_score": [0.0]})
    climate = pd.DataFrame(
        {"hex_id": ["c"], **_monthly_frame(70.0), **_zero_precip(), **_calm_wind()}
    )
    calculator = SeasonalOutdoorsCalculator()
    results = calculator.compute(parks, climate)
    assert results.loc[0, "SOU"] == 0
    assert results["SOU"].between(0, 100).all()


def test_extract_parks_score_from_categories() -> None:
    category_scores = pd.DataFrame(
        {
            "hex_id": ["a", "a", "b", "c"],
            "category": ["parks_trails", "restaurants", "parks_trails", "museums"],
            "score": [80.0, 10.0, 60.0, 20.0],
        }
    )
    parks = extract_parks_score(category_scores)
    assert set(parks.columns) == {"hex_id", "parks_score"}
    assert parks.loc[parks["hex_id"] == "a", "parks_score"].iloc[0] == 80.0
    assert parks.loc[parks["hex_id"] == "b", "parks_score"].iloc[0] == 60.0


def test_from_category_scores_handles_missing_category() -> None:
    category_scores = pd.DataFrame(
        {
            "hex_id": ["x", "y"],
            "category": ["restaurants", "bars"],
            "score": [30.0, 40.0],
        }
    )
    climate = pd.DataFrame(
        [
            {"hex_id": "x", **_monthly_frame(65.0), **_zero_precip(), **_calm_wind()},
            {"hex_id": "y", **_monthly_frame(65.0), **_zero_precip(), **_calm_wind()},
        ]
    )
    calculator = SeasonalOutdoorsCalculator(SeasonalOutdoorsConfig(parks_column="parks_score"))
    results = calculator.from_category_scores(category_scores, climate)
    assert (results["SOU"] == 0).all()


def test_harsh_winter_penalises_score() -> None:
    parks = pd.DataFrame({"hex_id": ["winter"], "parks_score": [90.0]})
    climate = pd.DataFrame(
        {
            "hex_id": ["winter"],
            **{f"temp_{month}": 15.0 for month in _all_months()},
            **{f"precip_{month}": 1.5 for month in _all_months()},
            **{f"wind_{month}": 25.0 for month in _all_months()},
        }
    )
    calculator = SeasonalOutdoorsCalculator()
    result = calculator.compute(parks, climate)
    assert result.loc[0, "SOU"] == pytest.approx(0.0)


def test_from_parks_data_integration() -> None:
    parks = pd.DataFrame(
        {
            "poi_id": ["p1", "p2"],
            "area_acres": [40.0, 5.0],
            "amenities": [4, 1],
            "designation": ["national_park", "city_park"],
        }
    )
    accessibility = pd.DataFrame(
        {
            "origin_hex": ["a", "a", "b"],
            "poi_id": ["p1", "p2", "p2"],
            "weight": [0.7, 0.3, 0.5],
        }
    )
    pleasant = {**_monthly_frame(68.0), **_zero_precip(), **_calm_wind()}
    harsh = {**_monthly_frame(95.0), **_zero_precip(), **_calm_wind()}
    climate = pd.DataFrame(
        [
            {"hex_id": "a", **pleasant},
            {"hex_id": "b", **harsh},
        ]
    )
    calculator = SeasonalOutdoorsCalculator(SeasonalOutdoorsConfig())
    results = calculator.from_parks_data(parks, accessibility, climate)
    assert set(results.columns) == {"hex_id", "SOU", "sigma_out"}
    pleasant_score = results.loc[results["hex_id"] == "a", "SOU"].iloc[0]
    harsh_score = results.loc[results["hex_id"] == "b", "SOU"].iloc[0]
    assert pleasant_score > harsh_score
    assert results["SOU"].between(0, 100).all()
