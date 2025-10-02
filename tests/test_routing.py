from pathlib import Path

import pandas as pd
import pytest

from Urban_Amenities2.cli.main import GreatCircleOSRM
from Urban_Amenities2.router.api import RoutingAPI
from Urban_Amenities2.router.batch import BatchConfig, SkimBuilder
from Urban_Amenities2.router.osrm import OSRMClient, OSRMConfig, RoutingError
from Urban_Amenities2.router.otp import OTPClient, OTPConfig, OTPError


class DummyOSRM:
    def __init__(self) -> None:
        self.route_calls = 0
        self.table_calls = 0

    def route(self, coords):
        self.route_calls += 1
        return {"duration": 600.0, "distance": 1000.0, "legs": []}

    def table(self, sources, destinations=None):
        self.table_calls += 1
        destinations = destinations or sources
        durations = [[60.0 * (i + j + 1) for j in range(len(destinations))] for i in range(len(sources))]
        distances = [[1000.0 * (i + j + 1) for j in range(len(destinations))] for i in range(len(sources))]
        return {"durations": durations, "distances": distances}


class StubResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


class StubSession:
    def __init__(self, responses: dict[str, dict]):
        self.responses = responses
        self.calls: list[str] = []

    def get(self, url: str, params=None, timeout: int | None = None):
        self.calls.append(url)
        if "route" in url:
            return StubResponse(self.responses["route"])
        return StubResponse(self.responses.get("table", {}))

    def post(self, url: str, json=None, timeout: int | None = None):
        self.calls.append(url)
        return StubResponse(self.responses["post"])


def test_great_circle_osrm() -> None:
    client = GreatCircleOSRM("car")
    route = client.route([(0.0, 0.0), (1.0, 1.0)])
    assert route["duration"] > 0
    matrix = client.table([(0.0, 0.0)], [(1.0, 1.0)])
    assert matrix["durations"][0][0] > 0


def test_routing_api_and_batch(tmp_path: Path) -> None:
    dummy = DummyOSRM()
    api = RoutingAPI({"car": dummy})
    origin = (-104.0, 39.0)
    destination = (-105.0, 39.5)
    result = api.route("car", origin, destination)
    assert result.duration_min > 0

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


def test_osrm_client_route_and_table() -> None:
    responses = {
        "route": {"code": "Ok", "routes": [{"duration": 100.0, "distance": 200.0, "legs": []}]},
        "table": {"code": "Ok", "durations": [[10.0]], "distances": [[20.0]]},
    }
    session = StubSession(responses)
    client = OSRMClient(OSRMConfig(base_url="http://osrm"), session=session)
    route = client.route([(0.0, 0.0), (1.0, 1.0)])
    assert route["duration"] == 100.0
    table = client.table([(0.0, 0.0)], [(1.0, 1.0)])
    assert table["durations"][0][0] == 10.0

    error_session = StubSession({"route": {"code": "Error", "message": "bad"}})
    client_error = OSRMClient(OSRMConfig(base_url="http://osrm"), session=error_session)
    with pytest.raises(RoutingError):
        client_error.route([(0.0, 0.0), (1.0, 1.0)])


def test_otp_client_parsing() -> None:
    itinerary = {
        "duration": 600,
        "walkTime": 120,
        "transitTime": 300,
        "waitingTime": 180,
        "transfers": 1,
        "fare": {"fare": {"regular": {"amount": 2.5}}},
        "legs": [
            {"mode": "WALK", "duration": 120, "distance": 200, "from": {"name": "A"}, "to": {"name": "B"}}
        ],
    }
    payload = {"data": {"plan": {"itineraries": [itinerary]}}}
    session = StubSession({"post": payload})
    client = OTPClient(OTPConfig(base_url="http://otp"), session=session)
    plans = client.plan_trip((0.0, 0.0), (1.0, 1.0), ["TRANSIT"])
    assert plans[0]["transit_time"] == 300

    error_session = StubSession({"post": {"errors": [{"message": "fail"}]}})
    client_error = OTPClient(OTPConfig(base_url="http://otp"), session=error_session)
    with pytest.raises(OTPError):
        client_error.plan_trip((0.0, 0.0), (1.0, 1.0), ["WALK"])
