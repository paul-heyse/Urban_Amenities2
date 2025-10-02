import pandas as pd

from Urban_Amenities2.scores.mobility_reliability import (
    MobilityReliabilityCalculator,
    MorrConfig,
    MorrWeights,
    compute_frequent_transit_exposure,
    compute_micromobility_presence,
    compute_network_redundancy,
    compute_on_time_reliability,
    compute_service_span,
)


def _hex_frame(hex_id: str, value: float) -> pd.DataFrame:
    return pd.DataFrame({"hex_id": [hex_id], "value": [value]})


def test_compute_frequent_transit_exposure() -> None:
    stops = pd.DataFrame(
        {
            "hex_id": ["a", "a", "b"],
            "headway_peak": [10.0, 25.0, 12.0],
            "distance_m": [200.0, 600.0, 300.0],
        }
    )
    result = compute_frequent_transit_exposure(stops)
    assert result.loc[result["hex_id"] == "a", "C1"].iloc[0] == 100.0
    assert result.loc[result["hex_id"] == "b", "C1"].iloc[0] == 100.0


def test_morr_aggregation() -> None:
    c1 = pd.DataFrame({"hex_id": ["a", "b"], "C1": [80.0, 20.0]})
    c2 = pd.DataFrame({"hex_id": ["a", "b"], "C2": [60.0, 40.0]})
    c3 = pd.DataFrame({"hex_id": ["a", "b"], "C3": [90.0, 30.0]})
    c4 = pd.DataFrame({"hex_id": ["a", "b"], "C4": [70.0, 20.0]})
    c5 = pd.DataFrame({"hex_id": ["a", "b"], "C5": [50.0, 10.0]})
    calculator = MobilityReliabilityCalculator(MorrConfig(weights=MorrWeights()))
    scores = calculator.compute(c1, c2, c3, c4, c5)
    assert scores.loc[scores["hex_id"] == "a", "MORR"].iloc[0] > scores.loc[scores["hex_id"] == "b", "MORR"].iloc[0]


def test_component_calculations_cover_edge_cases() -> None:
    services = pd.DataFrame(
        {
            "hex_id": ["a", "a"],
            "service_hours": [18.0, 6.0],
            "has_early": [1, 0],
            "has_late": [1, 0],
            "has_weekend": [1, 0],
        }
    )
    c2 = compute_service_span(services)
    assert c2["C2"].max() <= 100

    reliability = pd.DataFrame(
        {
            "hex_id": ["a", "a"],
            "on_time_pct": [95.0, 85.0],
            "frequency_weight": [10.0, 0.0],
        }
    )
    c3 = compute_on_time_reliability(reliability)
    assert c3["C3"].iloc[0] == 95.0

    redundancy = pd.DataFrame(
        {"hex_id": ["a"], "transit_routes": [4], "road_routes": [3]}
    )
    c4 = compute_network_redundancy(redundancy)
    assert 0 < c4["C4"].iloc[0] <= 100

    micro = pd.DataFrame(
        {"hex_id": ["a", "b"], "stations": [10, 0], "area_sqkm": [2.0, 2.0]}
    )
    c5 = compute_micromobility_presence(micro)
    assert c5.loc[c5["hex_id"] == "a", "C5"].iloc[0] == 100.0
