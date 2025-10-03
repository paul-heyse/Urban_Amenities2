from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, cast

from ...hex.aggregation import lines_to_hex
from ...logging_utils import get_logger

try:
    import geopandas as _geopandas
except ModuleNotFoundError:  # pragma: no cover
    raise

import pandas as pd
from shapely.geometry import LineString

gpd = cast(Any, _geopandas)

try:  # pragma: no cover
    from google.cloud import bigquery as _bigquery_module  # type: ignore[import]
except ModuleNotFoundError:  # pragma: no cover
    _bigquery_module = None


if TYPE_CHECKING:  # pragma: no cover
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

        def result(self) -> _QueryJobResult:  # pragma: no cover
            return self

        def to_dataframe(self, *, create_bqstorage_client: bool = False) -> pd.DataFrame:
            raise ModuleNotFoundError(
                "google.cloud.bigquery is required runtime dependency for this feature"
            )

    class _ClientStub:
        def __init__(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover
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
    def result(self) -> Any:  # pragma: no cover
        ...


class _BigQueryClient(Protocol):
    def query(self, query: str, job_config: Any | None = None) -> _BigQueryQueryJob: ...


LOGGER = get_logger("aucs.ingest.transportation")


@dataclass
class TransportationBigQueryConfig:
    project: str
    dataset: str
    table: str = "transportation_segments"

    def table_ref(self) -> str:
        return f"`{self.project}.{self.dataset}.{self.table}`"


ALLOWED_CLASSES = {"road", "footway", "cycleway"}


def build_transportation_query(
    config: TransportationBigQueryConfig, classes: Iterable[str] | None = None
) -> str:
    classes = set(classes or ALLOWED_CLASSES)
    where = " OR ".join([f"class = '{cls}'" for cls in classes])
    query = (
        "SELECT id, class, subtype, speed_limits, access_restrictions, connectors, geometry "
        f"FROM {config.table_ref()} WHERE {where}"
    )
    return query


def read_transportation_from_bigquery(
    config: TransportationBigQueryConfig,
    client: _BigQueryClient | None = None,
    classes: Iterable[str] | None = None,
) -> pd.DataFrame:
    bigquery_client: _BigQueryClient = client or cast(
        _BigQueryClient, bigquery.Client(project=config.project)
    )
    query = build_transportation_query(config, classes=classes)
    LOGGER.info("querying_overture_transport", query=query)
    result = bigquery_client.query(query)
    frame = result.result().to_dataframe(create_bqstorage_client=False)
    return pd.DataFrame(frame)


def read_transportation_from_cloud(path: str | Path) -> pd.DataFrame:
    import fsspec  # type: ignore[import-untyped]

    with fsspec.open(path, mode="rb") as handle:
        return pd.read_parquet(handle)


def filter_transportation(
    frame: pd.DataFrame, classes: Iterable[str] | None = None
) -> pd.DataFrame:
    classes = set(classes or ALLOWED_CLASSES)
    return frame[frame["class"].isin(classes)].copy()


def parse_geometry(frame: pd.DataFrame, geometry_column: str = "geometry") -> pd.DataFrame:
    converted = frame.copy()
    converted[geometry_column] = [_ensure_linestring(value) for value in converted[geometry_column]]
    return converted


def index_segments(frame: pd.DataFrame, resolution: int = 9) -> pd.DataFrame:
    parsed = parse_geometry(frame)
    return lines_to_hex(
        parsed, geometry_column="geometry", hex_column="hex_id", resolution=resolution
    )


def export_mode_geojson(frame: pd.DataFrame, path: Path, mode_column: str) -> None:
    gdf = gpd.GeoDataFrame(frame, geometry="geometry", crs="EPSG:4326")
    gdf = gdf[gdf[mode_column]].copy()
    if gdf.empty:
        LOGGER.warning("empty_network_export", path=str(path), mode=mode_column)
    path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(path=str(path), driver="GeoJSON")


def export_networks(
    frame: pd.DataFrame, output_root: Path = Path("data/processed")
) -> dict[str, Path]:
    mapping = {
        "car": ("mode_car", output_root / "network_car.geojson"),
        "foot": ("mode_foot", output_root / "network_foot.geojson"),
        "bike": ("mode_bike", output_root / "network_bike.geojson"),
    }
    for _, column in mapping.values():
        frame[column] = frame.get(column, False)
    for _mode, (column, path) in mapping.items():
        export_mode_geojson(frame, path, column)
    return {mode: path for mode, (_, path) in mapping.items()}


def determine_modes(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    frame["mode_car"] = frame["class"].isin({"road"})
    frame["mode_foot"] = frame["class"].isin({"road", "footway"})
    frame["mode_bike"] = frame["class"].isin({"road", "cycleway"})
    return frame


def prepare_transportation(frame: pd.DataFrame) -> pd.DataFrame:
    filtered = filter_transportation(frame)
    parsed = parse_geometry(filtered)
    modes = determine_modes(parsed)
    return modes


__all__ = [
    "TransportationBigQueryConfig",
    "build_transportation_query",
    "read_transportation_from_bigquery",
    "read_transportation_from_cloud",
    "filter_transportation",
    "parse_geometry",
    "index_segments",
    "determine_modes",
    "export_networks",
    "prepare_transportation",
]


def _ensure_linestring(value: LineString | str) -> LineString:
    if isinstance(value, LineString):
        return value
    if isinstance(value, str):
        from shapely import wkt

        geometry = wkt.loads(value)
        if not isinstance(geometry, LineString):
            raise TypeError("Geometry WKT must resolve to LineString")
        return geometry
    raise TypeError("Unsupported geometry type for transportation segment")
