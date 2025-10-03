"""Typed export utilities for AUCS data."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from importlib import import_module
from pathlib import Path
from typing import Any, cast

import structlog

from .export_types import (
    GeoJSONFeature,
    GeoJSONFeatureCollection,
    GeoJSONGeometry,
    GeoPandasModule,
    JsonValue,
    TabularData,
)

logger = structlog.get_logger()


def _h3() -> Any:
    return import_module("h3")


def _geopandas() -> GeoPandasModule:
    module = import_module("geopandas")
    return cast(GeoPandasModule, module)


def _polygon_module() -> Any:
    return import_module("shapely.geometry")


def _hex_boundary(hex_id: str) -> list[tuple[float, float]]:
    boundary = _h3().cell_to_boundary(str(hex_id))
    return [(float(lon), float(lat)) for lat, lon in boundary]


def _hex_centroid(hex_id: str) -> tuple[float, float]:
    lat, lon = _h3().cell_to_latlng(str(hex_id))
    return float(lat), float(lon)


def _boundary_ring(boundary: Sequence[tuple[float, float]]) -> list[list[float]]:
    ring = [[lon, lat] for lon, lat in boundary]
    if ring and ring[0] != ring[-1]:
        ring.append([ring[0][0], ring[0][1]])
    return ring


def _normalise_value(value: object) -> JsonValue:
    if value is None:
        return None
    if isinstance(value, (str, bool, int, float)):
        return cast(JsonValue, value)
    if hasattr(value, "item"):
        return _normalise_value(value.item())
    if isinstance(value, Mapping):
        return {str(key): _normalise_value(val) for key, val in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_normalise_value(item) for item in value]
    return str(value)


def _record_to_feature(record: Mapping[str, object]) -> GeoJSONFeature | None:
    hex_raw = record.get("hex_id")
    if not isinstance(hex_raw, str):
        return None
    boundary = _hex_boundary(hex_raw)
    coordinates = [_boundary_ring(boundary)]
    properties: dict[str, JsonValue] = {}
    for key, value in record.items():
        if key == "hex_id":
            properties[key] = hex_raw
            continue
        properties[key] = _normalise_value(value)
    geometry: GeoJSONGeometry = {
        "type": "Polygon",
        "coordinates": coordinates,
    }
    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": properties,
    }


def build_feature_collection(
    frame: TabularData,
    properties: Sequence[str] | None = None,
) -> GeoJSONFeatureCollection:
    requested = list(properties) if properties else [column for column in frame.columns if column != "hex_id"]
    columns = ["hex_id", *requested]
    subset_obj = frame[[column for column in columns if column in frame.columns]]
    subset = cast(TabularData, subset_obj)
    records = subset.to_dict("records")
    features: list[GeoJSONFeature] = []
    for record in records:
        feature = _record_to_feature(record)
        if feature is not None:
            features.append(feature)
    return {"type": "FeatureCollection", "features": features}


def export_geojson(
    frame: TabularData,
    output_path: Path,
    properties: Sequence[str] | None = None,
) -> Path:
    logger.info("export_geojson_start", rows=len(frame), output=str(output_path))
    collection = build_feature_collection(frame, properties=properties)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(collection))
    logger.info("export_geojson_complete", path=str(output_path))
    return output_path


def export_csv(
    frame: TabularData,
    output_path: Path,
    *,
    include_geometry: bool = False,
) -> Path:
    logger.info("export_csv_start", rows=len(frame), output=str(output_path))
    export_frame = frame.copy()
    if include_geometry and "lat" not in export_frame.columns:
        centroids = [
            _hex_centroid(str(hex_id))
            for hex_id in cast(Iterable[Any], export_frame["hex_id"])
        ]
        export_frame["lat"] = [lat for lat, _ in centroids]
        export_frame["lon"] = [lon for _, lon in centroids]
    export_frame.to_csv(str(output_path), index=False)
    logger.info("export_csv_complete", path=str(output_path))
    return output_path


def export_shapefile(frame: TabularData, output_path: Path) -> Path:
    logger.info("export_shapefile_start", rows=len(frame), output=str(output_path))
    geopandas = _geopandas()
    polygon_module = _polygon_module()
    geometries = [
        polygon_module.Polygon(_hex_boundary(str(hex_id)))
        for hex_id in cast(Iterable[Any], frame["hex_id"])
    ]
    geo_frame = geopandas.GeoDataFrame(frame, geometry=geometries, crs="EPSG:4326")
    rename_map = {column: column[:10] for column in geo_frame.columns}
    geo_frame.rename(columns=rename_map, inplace=True)
    geo_frame.to_file(str(output_path), driver="ESRI Shapefile")
    logger.info("export_shapefile_complete", path=str(output_path))
    return output_path


def export_parquet(frame: TabularData, output_path: Path) -> Path:
    logger.info("export_parquet_start", rows=len(frame), output=str(output_path))
    frame.to_parquet(str(output_path), compression="snappy", index=False)
    logger.info("export_parquet_complete", path=str(output_path))
    return output_path


def create_shareable_url(
    base_url: str,
    *,
    state: str | None = None,
    metro: str | None = None,
    subscore: str | None = None,
    zoom: int | None = None,
    center_lat: float | None = None,
    center_lon: float | None = None,
) -> str:
    from urllib.parse import urlencode

    params: dict[str, str | int | float] = {}

    if state:
        params["state"] = state
    if metro:
        params["metro"] = metro
    if subscore:
        params["subscore"] = subscore
    if zoom is not None:
        params["zoom"] = zoom
    if center_lat is not None and center_lon is not None:
        params["lat"] = center_lat
        params["lon"] = center_lon

    if not params:
        return base_url

    query_string = urlencode(params)
    return f"{base_url}?{query_string}"


__all__ = [
    "build_feature_collection",
    "create_shareable_url",
    "export_csv",
    "export_geojson",
    "export_parquet",
    "export_shapefile",
]

