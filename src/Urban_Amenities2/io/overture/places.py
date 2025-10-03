from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, cast

from ...dedupe.pois import DedupeConfig, deduplicate_pois
from ...hex.aggregation import points_to_hex
from ...logging_utils import get_logger
from ...xwalk.overture_aucs import CategoryMatcher, load_crosswalk

try:
    import geopandas as _geopandas
except ModuleNotFoundError:  # pragma: no cover
    raise

import pandas as pd
from shapely.geometry import Point

gpd = cast(Any, _geopandas)

try:  # pragma: no cover - optional dependency
    from google.cloud import bigquery as _bigquery_module  # type: ignore[import]
except ModuleNotFoundError:  # pragma: no cover - fallback stub
    _bigquery_module = None


if TYPE_CHECKING:  # pragma: no cover - mypy typing
    from google.cloud import bigquery as bigquery  # type: ignore[import]
else:

    class _ScalarQueryParameter:
        def __init__(self, name: str, param_type: str, value: str) -> None:
            self.name = name
            self.param_type = param_type
            self.value = value

    class _QueryJobConfig:
        def __init__(self) -> None:
            self.query_parameters: list[_ScalarQueryParameter] = []

    class _QueryJobResult:
        def __init__(self) -> None:
            raise ModuleNotFoundError(
                "google.cloud.bigquery is required runtime dependency for this feature"
            )

        def result(self) -> _QueryJobResult:  # pragma: no cover - stub path
            return self

        def to_dataframe(self, *, create_bqstorage_client: bool = False) -> pd.DataFrame:
            raise ModuleNotFoundError(
                "google.cloud.bigquery is required runtime dependency for this feature"
            )

    class _ClientStub:
        def __init__(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - stub
            raise ModuleNotFoundError(
                "google.cloud.bigquery is required runtime dependency for this feature"
            )

        def query(self, query: str, job_config: Any | None = None) -> _QueryJobResult:
            raise ModuleNotFoundError(
                "google.cloud.bigquery is required runtime dependency for this feature"
            )

    class _BigQueryStub:
        Client = _ClientStub
        QueryJobConfig = _QueryJobConfig
        ScalarQueryParameter = _ScalarQueryParameter

    bigquery = cast(Any, _bigquery_module or _BigQueryStub())


class _BigQueryQueryJob(Protocol):
    def result(self) -> Any:  # pragma: no cover - protocol stub
        ...


class _BigQueryClient(Protocol):
    def query(self, query: str, job_config: Any | None = None) -> _BigQueryQueryJob: ...


LOGGER = get_logger("aucs.ingest.overture")


BBox = tuple[float, float, float, float]


@dataclass
class BigQueryConfig:
    project: str
    dataset: str
    table: str = "places"

    def table_ref(self) -> str:
        return f"`{self.project}.{self.dataset}.{self.table}`"


def build_bigquery_query(
    config: BigQueryConfig, state: str | None = None, bbox: BBox | None = None
) -> str:
    where: list[str] = ["operating_status = 'open'"]
    if state:
        where.append("address_components.administrative_area = @state")
    if bbox:
        min_lon, min_lat, max_lon, max_lat = bbox
        where.append("ST_CONTAINS(ST_GEOGFROMTEXT(@bbox), geometry)")
    where_clause = " AND ".join(where)
    select_columns = [
        "id",
        "display.name AS name",
        "categories.primary AS primary_category",
        "categories.alternate AS alternate_categories",
        "brand",
        "confidence",
        "geometry.latitude AS lat",
        "geometry.longitude AS lon",
        "opening_hours",
        "operating_status",
    ]
    query = f"SELECT {', '.join(select_columns)} FROM {config.table_ref()} WHERE {where_clause}"
    return query


def read_places_from_bigquery(
    config: BigQueryConfig,
    client: _BigQueryClient | None = None,
    state: str | None = None,
    bbox: BBox | None = None,
) -> pd.DataFrame:
    bigquery_client: _BigQueryClient = client or cast(
        _BigQueryClient, bigquery.Client(project=config.project)
    )
    job_config = bigquery.QueryJobConfig()
    if state:
        job_config.query_parameters.append(bigquery.ScalarQueryParameter("state", "STRING", state))
    if bbox:
        polygon = _bbox_to_wkt(bbox)
        job_config.query_parameters.append(bigquery.ScalarQueryParameter("bbox", "STRING", polygon))
    query = build_bigquery_query(config, state=state, bbox=bbox)
    LOGGER.info("querying_overture_bigquery", query=query)
    job = bigquery_client.query(query, job_config=job_config)
    frame = job.result().to_dataframe(create_bqstorage_client=False)
    return pd.DataFrame(frame)


def read_places_from_cloud(path: str | Path, bbox: BBox | None = None) -> pd.DataFrame:
    import fsspec  # type: ignore[import-untyped]

    LOGGER.info("reading_overture_geo", path=str(path))
    with fsspec.open(path, mode="rb") as handle:
        frame = pd.read_parquet(handle)
    if bbox:
        frame = apply_bbox_filter(frame, bbox=bbox)
    return frame


def apply_bbox_filter(frame: pd.DataFrame, bbox: BBox) -> pd.DataFrame:
    min_lon, min_lat, max_lon, max_lat = bbox
    mask = (
        (frame["lon"] >= min_lon)
        & (frame["lon"] <= max_lon)
        & (frame["lat"] >= min_lat)
        & (frame["lat"] <= max_lat)
    )
    return frame[mask]


def filter_operating(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[frame.get("operating_status", "open") == "open"].copy()


def extract_fields(frame: pd.DataFrame) -> pd.DataFrame:
    columns = {
        "id": "poi_id",
        "name": "name",
        "categories": "categories",
        "primary_category": "primary_category",
        "alternate_categories": "alternate_categories",
        "brand": "brand",
        "confidence": "confidence",
        "lat": "lat",
        "lon": "lon",
        "opening_hours": "opening_hours",
    }
    extracted = frame[[col for col in columns if col in frame.columns]].rename(columns=columns)
    if "categories" not in extracted.columns and "primary_category" in extracted.columns:
        extracted["categories"] = extracted["primary_category"].apply(
            lambda value: [value] if isinstance(value, str) else []
        )
    return extracted


@dataclass
class PlacesPipeline:
    matcher: CategoryMatcher
    dedupe_config: DedupeConfig = field(default_factory=DedupeConfig)

    def run(
        self,
        frame: pd.DataFrame,
        output_path: Path | None = None,
        hex_resolution: int = 9,
    ) -> gpd.GeoDataFrame:
        working = filter_operating(frame)
        working = extract_fields(working)
        working = self.matcher.assign(
            working, primary_column="primary_category", alternate_column="alternate_categories"
        )
        deduped = deduplicate_pois(working, config=self.dedupe_config)
        hexed = points_to_hex(
            deduped,
            lat_column="lat",
            lon_column="lon",
            hex_column="hex_id",
            resolution=hex_resolution,
        )
        geo = gpd.GeoDataFrame(
            hexed,
            geometry=[
                Point(lon, lat) for lat, lon in zip(hexed["lat"], hexed["lon"], strict=False)
            ],
            crs="EPSG:4326",
        )
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            geo.to_parquet(output_path)
        return geo


def load_default_pipeline(
    crosswalk_path: Path | str = Path("docs/AUCS place category crosswalk"),
) -> PlacesPipeline:
    matcher = load_crosswalk(crosswalk_path)
    return PlacesPipeline(matcher=matcher)


def ingest_places(
    source: pd.DataFrame | str | Path,
    crosswalk_path: Path | str = Path("docs/AUCS place category crosswalk"),
    bbox: BBox | None = None,
    output_path: Path | None = Path("data/processed/pois.parquet"),
) -> gpd.GeoDataFrame:
    if isinstance(source, (str, Path)):
        frame = read_places_from_cloud(source, bbox=bbox)
    else:
        frame = source
        if bbox:
            frame = apply_bbox_filter(frame, bbox=bbox)
    pipeline = load_default_pipeline(crosswalk_path)
    return pipeline.run(frame, output_path=output_path)


def _bbox_to_wkt(bbox: BBox) -> str:
    min_lon, min_lat, max_lon, max_lat = bbox
    return f"POLYGON(({min_lon} {min_lat}, {max_lon} {min_lat}, {max_lon} {max_lat}, {min_lon} {max_lat}, {min_lon} {min_lat}))"


__all__ = [
    "BigQueryConfig",
    "build_bigquery_query",
    "read_places_from_bigquery",
    "read_places_from_cloud",
    "filter_operating",
    "extract_fields",
    "PlacesPipeline",
    "load_default_pipeline",
    "ingest_places",
]
