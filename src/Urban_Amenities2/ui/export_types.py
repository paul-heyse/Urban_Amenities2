from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping, Sequence
from pathlib import Path
from typing import (
    Any,
    Literal,
    Protocol,
    TypedDict,
    runtime_checkable,
)

JsonPrimitive = str | int | float | bool | None
JsonValue = JsonPrimitive | Sequence["JsonValue"] | Mapping[str, "JsonValue"]


class GeoJSONGeometry(TypedDict):
    type: Literal["Polygon"]
    coordinates: list[list[list[float]]]


class GeoJSONFeature(TypedDict):
    type: Literal["Feature"]
    geometry: GeoJSONGeometry
    properties: dict[str, JsonValue]


class GeoJSONFeatureCollection(TypedDict):
    type: Literal["FeatureCollection"]
    features: list[GeoJSONFeature]


class DownloadPayload(TypedDict, total=False):
    content: str
    filename: str
    type: str | None
    base64: Literal[True]


@runtime_checkable
class TabularSeries(Protocol):
    def __iter__(self) -> Iterator[Any]: ...

    def tolist(self) -> list[Any]: ...


@runtime_checkable
class TabularData(Protocol):
    columns: Sequence[str]

    def __len__(self) -> int: ...

    def copy(self) -> TabularData: ...

    def __getitem__(self, key: str | Sequence[str]) -> TabularSeries | TabularData: ...

    def __setitem__(self, key: str, value: Iterable[Any]) -> None: ...

    def to_csv(self, path: str | Path, *, index: bool = True) -> None: ...

    def to_parquet(
        self,
        path: str | Path,
        *,
        compression: str = "snappy",
        index: bool = True,
    ) -> None: ...

    def to_dict(self, orient: Literal["records"]) -> list[dict[str, Any]]: ...

    def rename(
        self,
        *,
        columns: Mapping[str, str] | None = None,
        inplace: bool = False,
    ) -> TabularData | None: ...


class GeoDataExporter(TabularData, Protocol):
    def to_file(self, path: str | Path, *, driver: str) -> None: ...


class GeoPandasModule(Protocol):
    def GeoDataFrame(
        self,
        data: TabularData,
        *,
        geometry: Sequence[Any],
        crs: str,
    ) -> GeoDataExporter: ...


class PandasModule(Protocol):
    def DataFrame(
        self, data: Mapping[str, Iterable[Any]] | Sequence[Mapping[str, Any]] | None = None
    ) -> TabularData: ...

    def read_parquet(self, path: Path, columns: Sequence[str] | None = None) -> TabularData: ...

    class Series(TabularSeries): ...


__all__ = [
    "DownloadPayload",
    "GeoDataExporter",
    "GeoJSONFeature",
    "GeoJSONFeatureCollection",
    "GeoJSONGeometry",
    "JsonPrimitive",
    "JsonValue",
    "PandasModule",
    "TabularData",
    "TabularSeries",
]
