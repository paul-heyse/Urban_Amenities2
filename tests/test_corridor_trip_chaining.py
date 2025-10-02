import pandas as pd

from Urban_Amenities2.scores.corridor_trip_chaining import CorridorConfig, CorridorTripChaining


def test_corridor_trip_chaining_filters_long_detours() -> None:
    chains = pd.DataFrame(
        {
            "hex_id": ["a", "a", "b", "c"],
            "quality": [50.0, 40.0, 100.0, 60.0],
            "likelihood": [0.4, 0.2, 0.9, 0.6],
            "detour_minutes": [5.0, 12.0, 4.0, 15.0],
        }
    )
    calculator = CorridorTripChaining(CorridorConfig(max_detour_minutes=10.0))
    result = calculator.compute(chains)
    assert set(result.columns) == {"hex_id", "CTE"}
    assert result.loc[result["hex_id"] == "a", "CTE"].iloc[0] > 0
    assert result.loc[result["hex_id"] == "a", "CTE"].iloc[0] < 100
    assert result.loc[result["hex_id"] == "b", "CTE"].iloc[0] == 100
    assert result.loc[result["hex_id"] == "c", "CTE"].iloc[0] == 0
