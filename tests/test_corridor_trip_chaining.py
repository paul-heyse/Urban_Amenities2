import pandas as pd

from Urban_Amenities2.scores.corridor_trip_chaining import CorridorConfig, CorridorTripChaining


def test_corridor_trip_chaining_filters_long_detours() -> None:
    chains = pd.DataFrame(
        {
            "hex_id": ["a", "a", "b"],
            "quality": [80.0, 70.0, 90.0],
            "likelihood": [0.8, 0.5, 0.3],
            "detour_minutes": [5.0, 12.0, 4.0],
        }
    )
    calculator = CorridorTripChaining(CorridorConfig(max_detour_minutes=10.0))
    result = calculator.compute(chains)
    assert set(result.columns) == {"hex_id", "CTE"}
    assert result.loc[result["hex_id"] == "a", "CTE"].iloc[0] > 0
    assert result.loc[result["hex_id"] == "a", "CTE"].iloc[0] < 100
    assert result.loc[result["hex_id"] == "b", "CTE"].iloc[0] == 100
