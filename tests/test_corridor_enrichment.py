from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from Urban_Amenities2.config.params import CorridorConfig
from Urban_Amenities2.scores.corridor_enrichment import (
    ErrandChainScorer,
    StopBufferBuilder,
    TransitPath,
    TransitPathIdentifier,
)
from Urban_Amenities2.scores.corridor_trip_chaining import (
    CorridorConfig as TripConfig,
    CorridorTripChaining,
)


@dataclass
class FakeOTPClient:
    responses: dict[tuple[tuple[float, float], tuple[float, float]], list[dict[str, object]]]
    calls: int = 0

    def plan_trip(
        self,
        origin: tuple[float, float],
        destination: tuple[float, float],
        modes: list[str],
        max_itineraries: int,
    ) -> list[dict[str, object]]:
        self.calls += 1
        return self.responses.get((origin, destination), [])[:max_itineraries]


def _itinerary(stop_count: int, duration_minutes: float, transfers: int = 0) -> dict[str, object]:
    legs = []
    for index in range(stop_count - 1):
        legs.append({"from": {"name": f"Stop{index}"}, "to": {"name": f"Stop{index+1}"}})
    return {"legs": legs, "duration": duration_minutes * 60, "transfers": transfers}


def _base_corridor_config() -> CorridorConfig:
    return CorridorConfig(
        max_paths=2,
        stop_buffer_m=350,
        detour_cap_min=10,
        pair_categories=[["groceries", "pharmacy"], ["bank", "post"]],
        walk_decay_alpha=0.25,
        major_hubs={
            "demo": [
                {"id": "hub", "name": "Downtown", "lat": 40.0, "lon": -105.0},
            ]
        },
        chain_weights={"groceries+pharmacy": 1.0, "bank+post": 0.7},
        min_stop_count=5,
        cache_size=16,
    )


def test_transit_path_identifier_filters_short_paths() -> None:
    config = _base_corridor_config()
    itinerary_long = _itinerary(stop_count=6, duration_minutes=30, transfers=1)
    itinerary_short = _itinerary(stop_count=3, duration_minutes=20)
    client = FakeOTPClient(
        responses={
            ((-104.0, 39.7), (-105.0, 40.0)): [itinerary_long, itinerary_short],
        }
    )
    identifier = TransitPathIdentifier(client, config, modes=["TRANSIT"])
    paths = identifier.identify_paths("hex1", (-104.0, 39.7), "demo")
    assert len(paths) == 1
    assert paths[0].stops[0] == "Stop0"
    assert client.calls == 1
    # Cached second call should not increase OTP queries.
    repeat = identifier.identify_paths("hex1", (-104.0, 39.7), "demo")
    assert len(repeat) == 1
    assert client.calls == 1


def test_stop_buffer_builder_collects_pois() -> None:
    config = _base_corridor_config()
    path = TransitPath(
        hex_id="hex1",
        hub_id="hub",
        path_index=0,
        stops=[f"Stop{i}" for i in range(6)],
        duration_minutes=30.0,
        transfers=0,
        score=1.0,
    )
    stops = pd.DataFrame(
        {
            "stop_id": [f"Stop{i}" for i in range(6)],
            "stop_name": [f"Stop{i}" for i in range(6)],
            "lon": np.linspace(-104.01, -104.05, 6),
            "lat": np.linspace(39.7, 39.74, 6),
        }
    )
    pois = pd.DataFrame(
        {
            "poi_id": ["p1", "p2", "p3"],
            "category": ["groceries", "pharmacy", "bank"],
            "quality": [80.0, 75.0, 60.0],
            "lon": [-104.0108, -104.012, -104.018],
            "lat": [39.701, 39.703, 39.709],
        }
    )
    builder = StopBufferBuilder(config.stop_buffer_m, ["groceries", "pharmacy", "bank", "post"])
    mapping = builder.collect([path], stops, pois)
    assert not mapping.empty
    assert {"poi_id", "distance_m", "walk_minutes"} <= set(mapping.columns)
    assert mapping["distance_m"].ge(0).all()
    # Deduplicate: each POI should appear once per path.
    assert mapping.drop_duplicates(subset=["poi_id"]).shape[0] == mapping.shape[0]


def test_errand_chain_scorer_creates_chains() -> None:
    config = _base_corridor_config()
    builder = StopBufferBuilder(config.stop_buffer_m, ["groceries", "pharmacy"])
    path = TransitPath(
        hex_id="hexX",
        hub_id="hub",
        path_index=0,
        stops=["Stop0", "Stop1", "Stop2", "Stop3", "Stop4"],
        duration_minutes=25.0,
        transfers=0,
        score=1.0,
    )
    stops = pd.DataFrame(
        {
            "stop_id": ["Stop0", "Stop1", "Stop2", "Stop3", "Stop4"],
            "stop_name": ["Stop0", "Stop1", "Stop2", "Stop3", "Stop4"],
            "lon": [-104.1, -104.11, -104.12, -104.13, -104.14],
            "lat": [39.7, 39.705, 39.71, 39.715, 39.72],
        }
    )
    pois = pd.DataFrame(
        {
            "poi_id": ["g1", "p1"],
            "category": ["groceries", "pharmacy"],
            "quality": [85.0, 70.0],
            "lon": [-104.1, -104.13],
            "lat": [39.701, 39.716],
        }
    )
    mapping = builder.collect([path], stops, pois)
    scorer = ErrandChainScorer(config)
    chains = scorer.score(mapping)
    assert not chains.empty
    assert set(["hex_id", "quality", "likelihood", "detour_minutes"]) <= set(chains.columns)
    assert chains["detour_minutes"].max() <= config.detour_cap_min

    trip_config = TripConfig()
    aggregator = CorridorTripChaining(trip_config)
    result = aggregator.compute(chains)
    assert set(result.columns) == {trip_config.hex_column, trip_config.output_column}
    assert result[trip_config.output_column].between(0, 100).all()
