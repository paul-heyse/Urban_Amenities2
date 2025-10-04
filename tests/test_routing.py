from collections.abc import Mapping
from pathlib import Path

import pandas as pd
import pytest

from Urban_Amenities2.cli.main import GreatCircleOSRM
from Urban_Amenities2.router.api import RoutingAPI
from Urban_Amenities2.router.batch import BatchConfig, SkimBuilder
from Urban_Amenities2.router.osrm import (
    OSRMClient,
    OSRMConfig,
    OSRMRoute,
    OSRMTable,
    RoutingError,
)
from Urban_Amenities2.router.otp import OTPClient, OTPConfig, OTPError

from .conftest import StubSession


class DummyOSRM:
    def __init__(self) -> None:
        self.route_calls = 0
        self.table_calls = 0

    def route(self, coords):
        self.route_calls += 1
        return OSRMRoute(duration=600.0, distance=1000.0, legs=[])

    def table(self, sources, destinations=None):
        self.table_calls += 1
        destinations = destinations or sources
        durations = [
            [60.0 * (i + j + 1) for j in range(len(destinations))] for i in range(len(sources))
        ]
        distances = [
            [1000.0 * (i + j + 1) for j in range(len(destinations))] for i in range(len(sources))
        ]
        return OSRMTable(durations=durations, distances=distances)


def test_great_circle_osrm() -> None:
    client = GreatCircleOSRM("car")
    route = client.route([(0.0, 0.0), (1.0, 1.0)])
    assert route.duration > 0
    assert isinstance(route, Mapping)
    assert route["duration"] == pytest.approx(route.duration)
    route_dict = dict(route)
    assert route_dict["distance"] == pytest.approx(route.distance)
    matrix = client.table([(0.0, 0.0)], [(1.0, 1.0)])
    assert matrix.durations[0][0] > 0
    assert isinstance(matrix, Mapping)
    assert matrix["durations"][0][0] == pytest.approx(matrix.durations[0][0])
    assert matrix["distances"][0][0] == pytest.approx(matrix.distances[0][0])


def test_routing_api_and_batch(tmp_path: Path) -> None:
    dummy = DummyOSRM()
    api = RoutingAPI({"car": dummy})
    origin = (-104.0, 39.0)
    destination = (-105.0, 39.5)
    result = api.route("car", origin, destination)
    assert result.duration_min > 0
    assert result.metadata["engine"] == "osrm"
    summary = result.metadata["summary"]
    assert summary["duration_min"] == pytest.approx(result.duration_min)
    assert summary["distance_m"] == pytest.approx(1000.0)
    assert result.metadata["legs"] == []

    matrix = api.matrix("car", [origin], [destination])
    assert not matrix.empty
    assert dummy.table_calls == 1

    builder = SkimBuilder(api, BatchConfig(cache_dir=tmp_path / "cache", mode="car"))
    skim1 = builder.matrix([origin], [destination])
    skim2 = builder.matrix([origin], [destination])
    assert dummy.table_calls == 2  # first API matrix + first builder call
    assert skim1.equals(skim2)
    output_path = tmp_path / "skims.parquet"
    builder.write_parquet(skim1, output_path)
    stored = pd.read_parquet(output_path)
    assert not stored.empty


def test_routing_api_accepts_mapping_payloads() -> None:
    class MappingOSRM:
        def route(self, coords):  # type: ignore[no-untyped-def]
            return {
                "duration": 180.0,
                "distance": 500.0,
                "legs": [{"duration": 60.0, "distance": 200.0}],
            }

        def table(self, sources, destinations=None):  # type: ignore[no-untyped-def]
            destinations = destinations or sources
            durations = [
                [float((i + j + 1) * 30.0) for j in range(len(destinations))]
                for i in range(len(sources))
            ]
            distances = [
                [float((i + j + 1) * 100.0) for j in range(len(destinations))]
                for i in range(len(sources))
            ]
            return {"durations": durations, "distances": distances}

    api = RoutingAPI({"car": MappingOSRM()})
    result = api.route("car", (0.0, 0.0), (1.0, 1.0))
    assert result.duration_min == pytest.approx(3.0)
    assert result.distance_m == pytest.approx(500.0)

    matrix = api.matrix("car", [(0.0, 0.0)], [(1.0, 1.0)])
    assert matrix.loc[0, "duration_min"] == pytest.approx(0.5)
    assert matrix.loc[0, "distance_m"] == pytest.approx(100.0)


def test_osrm_client_route_and_table(osrm_stub_session) -> None:
    client = OSRMClient(OSRMConfig(base_url="http://osrm"), session=osrm_stub_session)
    route = client.route([(0.0, 0.0), (1.0, 1.0)])
    assert route.duration == 100.0
    assert isinstance(route, Mapping)
    assert route["duration"] == pytest.approx(route.duration)
    assert route.get("distance") == pytest.approx(route.distance)
    table = client.table([(0.0, 0.0)], [(1.0, 1.0)])
    assert table.durations[0][0] == 10.0
    assert isinstance(table, Mapping)
    assert table["durations"][0][0] == pytest.approx(table.durations[0][0])
    distances = table.get("distances")
    if distances is not None and table.distances is not None:
        assert distances[0][0] == pytest.approx(table.distances[0][0])


def test_osrm_client_parses_leg_payloads(osrm_stub_session) -> None:
    osrm_stub_session.responses["route"]["routes"][0]["legs"] = [
        {"duration": 45, "distance": 120.0},
        {"duration": 30, "distance": None},
    ]
    client = OSRMClient(OSRMConfig(base_url="http://osrm"), session=osrm_stub_session)
    route = client.route([(0.0, 0.0), (1.0, 1.0)])
    assert [leg.duration for leg in route.legs] == [45.0, 30.0]
    assert route.legs[1].distance is None


def test_osrm_client_handles_missing_distances(osrm_stub_session) -> None:
    osrm_stub_session.responses["table"] = {"code": "Ok", "durations": [[15.0]]}
    client = OSRMClient(OSRMConfig(base_url="http://osrm"), session=osrm_stub_session)
    table = client.table([(0.0, 0.0)], [(1.0, 1.0)])
    assert table.distances is None

    error_session = StubSession({"route": {"code": "Error", "message": "bad"}})
    client_error = OSRMClient(OSRMConfig(base_url="http://osrm"), session=error_session)
    with pytest.raises(RoutingError):
        client_error.route([(0.0, 0.0), (1.0, 1.0)])

    malformed_session = StubSession({"route": []})
    malformed_client = OSRMClient(OSRMConfig(base_url="http://osrm"), session=malformed_session)
    with pytest.raises(RoutingError):
        malformed_client.route([(0.0, 0.0), (1.0, 1.0)])


def test_otp_client_parsing(otp_stub_session) -> None:
    client = OTPClient(OTPConfig(base_url="http://otp"), session=otp_stub_session)
    plans = client.plan_trip((0.0, 0.0), (1.0, 1.0), ["TRANSIT"])
    assert plans[0]["transit_time"] == 300
    request_record = otp_stub_session.requests[-1]
    assert request_record["method"] == "POST"
    variables = request_record["json"]["variables"]
    assert variables["modes"] == ["TRANSIT"]
    assert variables["numItineraries"] == 3

    error_session = StubSession({"post": {"errors": [{"message": "fail"}]}})
    client_error = OTPClient(OTPConfig(base_url="http://otp"), session=error_session)
    with pytest.raises(OTPError):
        client_error.plan_trip((0.0, 0.0), (1.0, 1.0), ["WALK"])

    empty_session = StubSession({"post": {"data": {"plan": {"itineraries": None}}}})
    client_empty = OTPClient(OTPConfig(base_url="http://otp"), session=empty_session)
    assert client_empty.plan_trip((0.0, 0.0), (1.0, 1.0), ["TRANSIT"]) == []

    malformed_session = StubSession({"post": ("invalid", 200)})
    malformed_client = OTPClient(OTPConfig(base_url="http://otp"), session=malformed_session)
    with pytest.raises(OTPError):
        malformed_client.plan_trip((0.0, 0.0), (1.0, 1.0), ["TRANSIT"])  # type: ignore[arg-type]


def test_osrm_table_batches_concatenate_results() -> None:
    class RecordingOSRM(OSRMClient):
        def __init__(self, include_distances: bool = True):
            super().__init__(OSRMConfig(base_url="http://osrm", max_matrix=2))
            self.include_distances = include_distances
            self.calls: list[tuple[str, dict[str, object] | None]] = []

        def _request(self, path: str, params: dict[str, object] | None = None) -> dict:
            self.calls.append((path, params))
            assert params is not None
            source_count = len(str(params["sources"]).split(";"))
            dest_count = len(str(params["destinations"]).split(";"))
            durations = [
                [float(i * dest_count + j + 1) for j in range(dest_count)]
                for i in range(source_count)
            ]
            payload: dict[str, object] = {"code": "Ok", "durations": durations}
            if self.include_distances:
                payload["distances"] = [[value * 100.0 for value in row] for row in durations]
            return payload

    origins = [(-104.0, 39.0), (-105.0, 39.5), (-106.0, 40.0)]
    destinations = [(-104.5, 39.1), (-105.5, 39.6), (-106.5, 40.1)]
    client = RecordingOSRM()
    matrix = client.table(origins, destinations)
    assert len(matrix.durations) == len(origins)
    assert len(matrix.durations[0]) == len(destinations)
    assert len(client.calls) == 4  # 2x2 batching grid

    client_missing_distances = RecordingOSRM(include_distances=False)
    matrix_missing = client_missing_distances.table(origins, destinations)
    assert matrix_missing.distances is None


def test_routing_matrix_handles_missing_distances() -> None:
    class DurationOnlyOSRM(OSRMClient):
        def __init__(self) -> None:
            super().__init__(OSRMConfig(base_url="http://osrm"))

        def table(self, sources, destinations=None):  # type: ignore[override]
            destinations = destinations or sources
            durations = [[60.0 for _ in destinations] for _ in sources]
            return OSRMTable(durations=durations, distances=None)

    api = RoutingAPI({"car": DurationOnlyOSRM()})
    origins = [(-104.0, 39.0), (-105.0, 39.5)]
    destinations = [(-104.5, 39.1)]
    frame = api.matrix("car", origins, destinations)
    assert frame["duration_min"].notna().all()
    assert frame["distance_m"].isna().all()


def test_routing_transit_requires_itinerary() -> None:
    api = RoutingAPI(
        {"car": DummyOSRM()},
        otp_client=type("EmptyOTP", (), {"plan_trip": lambda self, *args, **kwargs: []})(),
    )
    with pytest.raises(ValueError):
        api.route("transit", (-104.0, 39.0), (-105.0, 39.5))


def test_routing_api_selects_shortest_transit_itinerary() -> None:
    class DummyOTPShortest:
        def plan_trip(self, *args, **kwargs):  # type: ignore[no-untyped-def]
            return [
                {
                    "duration": 1800.0,
                    "walk_time": 120.0,
                    "transit_time": 900.0,
                    "wait_time": 300.0,
                    "legs": [],
                },
                {
                    "duration": 900.0,
                    "walk_time": 60.0,
                    "transit_time": 600.0,
                    "wait_time": 180.0,
                    "legs": [],
                },
            ]

    api = RoutingAPI({"car": DummyOSRM()}, otp_client=DummyOTPShortest())
    result = api.route("transit", (0.0, 0.0), (1.0, 1.0))
    assert result.duration_min == pytest.approx(15.0)
    summary = result.metadata["summary"]
    assert summary["transit_time_min"] == pytest.approx(10.0)


def test_routing_matrix_requires_supported_mode() -> None:
    api = RoutingAPI({"car": DummyOSRM()})
    with pytest.raises(ValueError):
        api.matrix("bike", [(0.0, 0.0)], [(1.0, 1.0)])


def test_routing_route_requires_known_mode() -> None:
    api = RoutingAPI({"car": DummyOSRM()})
    with pytest.raises(ValueError):
        api.route("rail", (0.0, 0.0), (1.0, 1.0))


def test_routing_transit_metadata_contract() -> None:
    class DummyOTP:
        def plan_trip(self, *args, **kwargs):
            return [
                {
                    "duration": 900.0,
                    "walk_time": 180.0,
                    "transit_time": 600.0,
                    "wait_time": 120.0,
                    "transfers": 1,
                    "fare": 2.5,
                    "legs": [
                        {
                            "mode": "WALK",
                            "duration": 180.0,
                            "distance": 250.0,
                            "from": "Start",
                            "to": "Station",
                        },
                        {
                            "mode": "BUS",
                            "duration": 600.0,
                            "distance": 5000.0,
                            "from": "Station",
                            "to": "End",
                        },
                    ],
                }
            ]

    api = RoutingAPI({"car": DummyOSRM()}, otp_client=DummyOTP())
    origin = (-104.0, 39.0)
    destination = (-105.0, 39.5)
    result = api.route("transit", origin, destination)
    metadata = result.metadata
    assert metadata["engine"] == "otp"
    summary = metadata["summary"]
    assert summary["duration_min"] == pytest.approx(15.0)
    assert summary["walk_time_min"] == pytest.approx(3.0)
    assert summary["transit_time_min"] == pytest.approx(10.0)
    assert summary["wait_time_min"] == pytest.approx(2.0)
    assert summary["transfers"] == 1
    assert summary["fare_usd"] == pytest.approx(2.5)
    legs = metadata["legs"]
    assert len(legs) == 2
    assert legs[0]["mode"] == "WALK"
    assert legs[0]["duration_min"] == pytest.approx(3.0)
    assert legs[0]["distance_m"] == pytest.approx(250.0)
    assert legs[0]["from"] == "Start"
    assert legs[0]["to"] == "Station"
