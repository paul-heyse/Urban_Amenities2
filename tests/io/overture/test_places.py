from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest
from shapely.geometry import Point

from Urban_Amenities2.io.overture import places


class StubBigQueryJob:
    def __init__(self, frame: pd.DataFrame) -> None:
        self._frame = frame
        self.requested = False

    def result(self) -> StubBigQueryJob:
        self.requested = True
        return self

    def to_dataframe(self, *, create_bqstorage_client: bool = False) -> pd.DataFrame:
        assert create_bqstorage_client is False
        return self._frame


class RecordingBigQueryClient:
    def __init__(self, frame: pd.DataFrame) -> None:
        self.frame = frame
        self.last_query: str | None = None
        self.last_config: Any | None = None

    def query(self, query: str, job_config: Any | None = None) -> StubBigQueryJob:
        self.last_query = query
        self.last_config = job_config
        return StubBigQueryJob(self.frame)


class StubMatcher:
    def assign(
        self,
        frame: pd.DataFrame,
        primary_column: str = "primary_category",
        alternate_column: str = "alternate_categories",
        output_column: str = "aucstype",
    ) -> pd.DataFrame:
        assigned = frame.copy()
        assigned[output_column] = assigned.get(primary_column, "").fillna("uncategorized").str.upper()
        assigned[f"{output_column}_group"] = "group"
        assigned[f"{output_column}_notes"] = None
        return assigned


@pytest.fixture(autouse=True)
def patch_points_to_hex(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_points_to_hex(frame: pd.DataFrame, **_: Any) -> pd.DataFrame:
        frame = frame.copy()
        frame["hex_id"] = [f"hex-{idx}" for idx in range(len(frame))]
        return frame

    monkeypatch.setattr(places, "points_to_hex", _fake_points_to_hex)


def test_build_bigquery_query_supports_state_and_bbox() -> None:
    config = places.BigQueryConfig(project="proj", dataset="data", table="places")
    query = places.build_bigquery_query(
        config,
        state="CO",
        bbox=(-105.0, 39.5, -104.5, 40.0),
    )
    assert "`proj.data.places`" in query
    assert "administrative_area = @state" in query
    assert "ST_CONTAINS" in query


def test_read_places_from_bigquery_uses_parameters(monkeypatch: pytest.MonkeyPatch) -> None:
    frame = pd.DataFrame(
        {
            "id": ["1"],
            "geometry.latitude": [40.0],
            "geometry.longitude": [-105.0],
        }
    )
    client = RecordingBigQueryClient(frame)
    config = places.BigQueryConfig(project="proj", dataset="data")
    result = places.read_places_from_bigquery(
        config,
        client=client,  # type: ignore[arg-type]
        state="CO",
        bbox=(-105.0, 39.5, -104.5, 40.0),
    )
    assert not result.empty
    assert client.last_query is not None and "WHERE" in client.last_query
    assert client.last_config is not None
    assert "@state" in client.last_query
    assert "@bbox" in client.last_query


def test_read_places_handles_large_result_sets() -> None:
    frame = pd.DataFrame(
        {
            "id": [str(i) for i in range(10005)],
            "geometry.latitude": [40.0] * 10005,
            "geometry.longitude": [-105.0] * 10005,
        }
    )
    client = RecordingBigQueryClient(frame)
    config = places.BigQueryConfig(project="proj", dataset="data")
    result = places.read_places_from_bigquery(config, client=client)  # type: ignore[arg-type]
    assert len(result) == 10005


def test_extract_fields_generates_category_list() -> None:
    frame = pd.DataFrame(
        {
            "id": ["poi-1"],
            "name": ["Cafe"],
            "primary_category": ["food.cafe"],
            "lat": [40.1],
            "lon": [-105.2],
        }
    )
    extracted = places.extract_fields(frame)
    assert extracted.loc[0, "categories"] == ["food.cafe"]


def test_apply_bbox_filter_excludes_missing_geometries() -> None:
    frame = pd.DataFrame(
        {
            "lon": [-105.1, np.nan, -104.9],
            "lat": [40.0, 40.0, np.nan],
        }
    )
    filtered = places.apply_bbox_filter(frame, bbox=(-106.0, 39.0, -104.0, 41.0))
    assert len(filtered) == 1


def test_pipeline_deduplicates_and_creates_geometry(monkeypatch: pytest.MonkeyPatch) -> None:
    data = pd.DataFrame(
        {
            "id": ["a", "b", "c"],
            "name": ["Cafe", "Cafe", "Library"],
            "primary_category": ["food.cafe", "food.cafe", "civic.library"],
            "alternate_categories": [["coffee"], ["coffee"], [["books"]]],
            "lat": [40.0, 40.0, 39.5],
            "lon": [-105.0, -105.0, -104.9],
            "operating_status": ["open", "open", "closed"],
        }
    )

    def _dedupe(frame: pd.DataFrame, **_: Any) -> pd.DataFrame:
        return frame.drop_duplicates(subset=["lat", "lon"])

    monkeypatch.setattr(places, "deduplicate_pois", _dedupe)
    matcher = StubMatcher()
    pipeline = places.PlacesPipeline(matcher=matcher)
    result = pipeline.run(data)
    assert set(result["poi_id"]) == {"a"}
    assert isinstance(result.geometry.iloc[0], Point)


def test_ingest_places_accepts_dataframe(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    data = pd.DataFrame(
        {
            "id": ["a"],
            "name": ["Cafe"],
            "primary_category": ["food.cafe"],
            "lat": [40.0],
            "lon": [-105.0],
            "operating_status": ["open"],
        }
    )
    monkeypatch.setattr(places, "load_default_pipeline", lambda *_: places.PlacesPipeline(matcher=StubMatcher()))
    monkeypatch.setattr(places, "deduplicate_pois", lambda frame, **_: frame)
    output = tmp_path / "pois.parquet"
    result = places.ingest_places(data, output_path=output)
    assert output.exists()
    assert not result.empty
