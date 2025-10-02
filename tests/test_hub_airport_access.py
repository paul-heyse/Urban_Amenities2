import pandas as pd
import pytest

from Urban_Amenities2.config.loader import load_params
from Urban_Amenities2.scores.hub_airport_access import (
    AccessibilityConfig,
    HubMassWeights,
    MuhAAConfig,
    MuhAAScore,
    compute_airport_accessibility,
    compute_hub_mass,
)


def test_compute_hub_mass_normalises_components() -> None:
    hubs = pd.DataFrame(
        {
            "hub_id": ["den", "slc"],
            "population": [2_900_000, 1_200_000],
            "gdp": [210, 120],
            "poi": [15000, 8000],
            "culture": [120, 60],
        }
    )
    masses = compute_hub_mass(hubs, HubMassWeights())
    assert set(masses.columns) == {"hub_id", "mass"}
    assert masses["mass"].between(0, 100).all()
    assert masses.loc[masses["hub_id"] == "den", "mass"].iloc[0] > masses.loc[masses["hub_id"] == "slc", "mass"].iloc[0]


def test_muhaa_combines_hub_and_airport_access() -> None:
    hubs = pd.DataFrame(
        {
            "hub_id": ["den", "slc"],
            "population": [2_900_000, 1_200_000],
            "gdp": [210, 120],
            "poi": [15000, 8000],
            "culture": [120, 60],
        }
    )
    hub_travel = pd.DataFrame(
        {
            "hex_id": ["h1", "h1", "h2", "h2"],
            "destination_id": ["den", "slc", "den", "slc"],
            "travel_minutes": [20, 60, 45, 30],
        }
    )
    airports = pd.DataFrame(
        {
            "airport_id": ["den", "slc"],
            "enplanements": [69_000_000, 26_000_000],
        }
    )
    airport_travel = pd.DataFrame(
        {
            "hex_id": ["h1", "h2"],
            "destination_id": ["den", "slc"],
            "travel_minutes": [25, 35],
        }
    )
    muhaa = MuhAAScore(MuhAAConfig(hub_contribution=0.6, airport_contribution=0.4))
    scores = muhaa.compute(hubs, hub_travel, airports, airport_travel)
    assert set(scores.columns) == {"hex_id", "MUHAA", "accessibility_hub", "accessibility_airport"}
    assert scores["MUHAA"].between(0, 100).all()
    assert scores.loc[scores["hex_id"] == "h1", "MUHAA"].iloc[0] > scores.loc[scores["hex_id"] == "h2", "MUHAA"].iloc[0]


def test_muhaa_from_params_loads_configuration() -> None:
    params, _ = load_params("configs/params_default.yml")
    muhaa = MuhAAScore.from_params(params)
    weights = muhaa.config.hub_weights.normalised()
    assert pytest.approx(weights["population"], rel=1e-6) == 0.4
    assert pytest.approx(muhaa.config.hub_alpha, rel=1e-6) == params.hubs_airports.hub_decay_alpha
    assert pytest.approx(muhaa.config.airport_contribution + muhaa.config.hub_contribution, rel=1e-6) == 1.0


def test_airport_specific_weights_adjust_mass() -> None:
    travel = pd.DataFrame(
        {
            "hex_id": ["h1", "h2"],
            "destination_id": ["den", "slc"],
            "travel_minutes": [20, 40],
        }
    )
    airports = pd.DataFrame(
        {
            "airport_id": ["den", "slc"],
            "enplanements": [60_000_000, 20_000_000],
        }
    )
    base = compute_airport_accessibility(travel, airports, config=AccessibilityConfig(), alpha=0.02)
    weighted = compute_airport_accessibility(
        travel,
        airports,
        config=AccessibilityConfig(),
        alpha=0.02,
        airport_weights={"den": 2.0},
    )
    assert weighted.loc[weighted["hex_id"] == "h1", "accessibility"].iloc[0] >= base.loc[base["hex_id"] == "h1", "accessibility"].iloc[0]
