"""Utilities for loading and caching model output data for the UI."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from importlib import import_module
from pathlib import Path
from typing import Any, Callable, cast

import pandas as pd

shapely_wkt: Any | None = None
shapely_mapping: Callable[[Any], dict[str, Any]] | None = None
unary_union: Callable[[Sequence[Any]], Any] | None = None

try:  # pragma: no cover - optional dependency handled gracefully
    from shapely import wkt as _shapely_wkt
    from shapely.geometry import mapping as _shapely_mapping
    from shapely.ops import unary_union as _shapely_union
except ImportError:  # pragma: no cover - shapely is an optional runtime dependency
    pass
else:
    shapely_wkt = _shapely_wkt
    shapely_mapping = _shapely_mapping
    unary_union = _shapely_union

from ..logging_utils import get_logger
from .config import UISettings
from .hexes import HexGeometryCache, build_hex_index
from .types import (
    AggregationCacheKey,
    Bounds,
    FeatureCollection,
    GeoJSONFeature,
    GeoJSONGeometry,
    OverlayMap,
    SummaryRow,
    empty_feature_collection,
)

LOGGER = get_logger("ui.data")

REQUIRED_COLUMNS: dict[str, set[str]] = {
    "scores": {"hex_id", "aucs", "EA", "LCA", "MUHAA", "JEA", "MORR", "CTE", "SOU"},
    "metadata": {"hex_id", "state", "metro", "county"},
}


def _require_columns(frame: pd.DataFrame, required: Iterable[str]) -> None:
    missing = [column for column in required if column not in frame.columns]
    if missing:
        msg = f"DataFrame missing required columns: {missing}"
        raise KeyError(msg)


def _import_h3() -> Any:
    """Import h3 lazily to keep optional dependency lightweight."""

    return import_module("h3")


@dataclass(slots=True)
class DatasetVersion:
    identifier: str
    created_at: datetime
    path: Path

    @classmethod
    def from_path(cls, path: Path) -> DatasetVersion:
        stat = path.stat()
        identifier = path.stem
        created_at = datetime.fromtimestamp(stat.st_mtime)
        return cls(identifier=identifier, created_at=created_at, path=path)


@dataclass(slots=True)
class DataContext:
    """Holds loaded datasets and derived aggregates for the UI."""

    settings: UISettings
    scores: pd.DataFrame = field(default_factory=pd.DataFrame)
    metadata: pd.DataFrame = field(default_factory=pd.DataFrame)
    geometries: pd.DataFrame = field(default_factory=pd.DataFrame)
    version: DatasetVersion | None = None
    hex_cache: HexGeometryCache = field(default_factory=HexGeometryCache)
    base_resolution: int | None = None
    bounds: Bounds | None = None
    _aggregation_cache: dict[AggregationCacheKey, pd.DataFrame] = field(default_factory=dict)
    _aggregation_version: str | None = None
    overlays: OverlayMap = field(default_factory=dict)
    _overlay_version: str | None = None

    @classmethod
    def from_settings(cls, settings: UISettings) -> DataContext:
        context = cls(settings=settings)
        context.refresh()
        return context

    def refresh(self) -> None:
        """Reload parquet files if a newer version is available."""

        data_path = self.settings.data_path
        if not data_path.exists():
            LOGGER.warning("ui_data_path_missing", path=str(data_path))
            return

        parquet_files = sorted(
            data_path.glob("*.parquet"), key=lambda p: p.stat().st_mtime, reverse=True
        )
        if not parquet_files:
            LOGGER.warning("ui_no_parquet", path=str(data_path))
            return

        latest = DatasetVersion.from_path(parquet_files[0])
        if self.version and latest.created_at <= self.version.created_at:
            return

        LOGGER.info("ui_loading_dataset", version=latest.identifier)
        self.scores = self._load_parquet(latest.path, columns=None)
        _require_columns(self.scores, REQUIRED_COLUMNS["scores"])
        metadata_path = data_path / "metadata.parquet"
        if metadata_path.exists():
            self.metadata = self._load_parquet(metadata_path)
            _require_columns(self.metadata, REQUIRED_COLUMNS["metadata"])
        else:
            self.metadata = pd.DataFrame()
        if not self.metadata.empty:
            self.scores = self.scores.merge(self.metadata, on="hex_id", how="left")
        self.version = latest
        self._aggregation_cache.clear()
        self._aggregation_version = latest.identifier
        self._prepare_geometries()
        self.validate_geometries()
        self._record_base_resolution()
        self._build_overlays(force=True)

    def _prepare_geometries(self) -> None:
        if "hex_id" not in self.scores.columns:
            return
        hex_ids = cast(Sequence[str], self.scores["hex_id"].astype(str).unique())
        geometries = self.hex_cache.ensure_geometries(hex_ids)
        self.geometries = geometries
        self._update_bounds()

    def validate_geometries(self) -> None:
        if "hex_id" not in self.scores.columns:
            return
        self.hex_cache.validate(self.scores["hex_id"].astype(str).tolist())

    def _load_parquet(self, path: Path, columns: Iterable[str] | None = None) -> pd.DataFrame:
        frame = pd.read_parquet(path, columns=list(columns) if columns else None)
        if "hex_id" in frame.columns:
            frame["hex_id"] = frame["hex_id"].astype("category")
        return frame

    def load_subset(self, columns: Iterable[str]) -> pd.DataFrame:
        """Return a view of the scores table restricted to specific columns."""

        if self.scores.empty:
            return self.scores
        unique_columns = list(dict.fromkeys(columns))
        subset = self.scores[unique_columns].copy()
        return subset

    def filter_scores(
        self,
        *,
        state: Iterable[str] | None = None,
        metro: Iterable[str] | None = None,
        county: Iterable[str] | None = None,
        score_range: tuple[float, float] | None = None,
    ) -> pd.DataFrame:
        frame = self.scores
        if frame.empty or self.metadata.empty:
            return frame
        mask = pd.Series(True, index=frame.index)
        if state:
            state_mask = frame["state"].isin(state)
            mask &= state_mask
        if metro:
            mask &= frame["metro"].isin(metro)
        if county:
            mask &= frame["county"].isin(county)
        if score_range:
            low, high = score_range
            mask &= frame["aucs"].between(low, high)
        return frame[mask]

    def summarise(self, columns: Iterable[str] | None = None) -> pd.DataFrame:
        if self.scores.empty:
            return pd.DataFrame()
        columns = (
            list(columns)
            if columns
            else ["aucs", "EA", "LCA", "MUHAA", "JEA", "MORR", "CTE", "SOU"]
        )
        summary: dict[str, SummaryRow] = {}
        percentiles = [p / 100.0 for p in self.settings.summary_percentiles]
        for column in columns:
            if column not in self.scores.columns:
                continue
            series = self.scores[column]
            stats: dict[str, float] = {
                "min": float(series.min()),
                "max": float(series.max()),
                "mean": float(series.mean()),
            }
            for percentile in percentiles:
                label = f"p{int(percentile * 100)}"
                stats[label] = float(series.quantile(percentile))
            summary[column] = cast(SummaryRow, stats)
        return pd.DataFrame(summary).T

    def export_geojson(self, path: Path, columns: Iterable[str] | None = None) -> Path:
        columns = list(columns) if columns else ["hex_id", "aucs"]
        frame = self.load_subset(columns + ["hex_id"])
        payload = self.to_geojson(frame)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload))
        return path

    def to_geojson(self, frame: pd.DataFrame) -> FeatureCollection:
        geometries = self.geometries
        if geometries.empty:
            raise RuntimeError("Hex geometries not initialised")
        merged = frame.merge(geometries, on="hex_id", how="left")
        features: list[GeoJSONFeature] = []
        for record in merged.to_dict("records"):
            data = dict(record)
            geometry_raw = data.pop("geometry")
            geometry = cast(GeoJSONGeometry, json.loads(cast(str, geometry_raw)))
            properties: dict[str, object] = {str(key): value for key, value in data.items()}
            features.append(
                {
                    "type": "Feature",
                    "geometry": geometry,
                    "properties": properties,
                }
            )
        return {"type": "FeatureCollection", "features": features}

    def export_csv(self, path: Path, columns: Iterable[str] | None = None) -> Path:
        columns = list(columns) if columns else ["hex_id", "aucs", "EA", "LCA"]
        frame = self.load_subset(columns)
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(path, index=False)
        return path

    def export_shapefile(self, path: Path, columns: Iterable[str] | None = None) -> Path:
        geopandas = __import__("geopandas")
        columns = list(columns) if columns else ["hex_id", "aucs"]
        frame = self.load_subset(columns + ["hex_id"])
        geometries = self.geometries
        if geometries.empty:
            raise RuntimeError("Hex geometries not initialised")
        merged = frame.merge(geometries, on="hex_id", how="left")
        gdf = geopandas.GeoDataFrame(
            merged.drop(columns=["geometry"]),
            geometry=geopandas.GeoSeries.from_wkt(merged["geometry_wkt"]),
            crs="EPSG:4326",
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        gdf.to_file(path)
        return path

    def get_hex_index(self, resolution: int) -> Mapping[str, list[str]]:
        if self.geometries.empty:
            return {}
        return build_hex_index(self.geometries, resolution)

    def aggregate_by_resolution(
        self, resolution: int, columns: Iterable[str] | None = None
    ) -> pd.DataFrame:
        if self.scores.empty:
            return pd.DataFrame()
        columns = list(dict.fromkeys(columns or ["aucs"]))
        subset_columns = ["hex_id", *columns]
        subset = self.scores[subset_columns].copy()
        if subset.empty:
            return subset
        subset["hex_id"] = subset["hex_id"].astype(str)
        h3 = _import_h3()
        subset["parent_hex"] = [
            cast(str, h3.cell_to_parent(hex_id, resolution)) for hex_id in subset["hex_id"]
        ]
        aggregations = {column: "mean" for column in columns if column in subset.columns}
        aggregations["hex_id"] = "count"
        frame = (
            subset.groupby("parent_hex", as_index=False)
            .agg(aggregations)
            .rename(columns={"parent_hex": "hex_id", "hex_id": "count"})
        )
        if frame.empty:
            return frame
        new_geoms = self.hex_cache.ensure_geometries(frame["hex_id"].astype(str).tolist())
        if self.geometries.empty:
            self.geometries = new_geoms
        else:
            self.geometries = (
                pd.concat([self.geometries, new_geoms])
                .drop_duplicates(subset=["hex_id"], keep="last")
                .reset_index(drop=True)
            )
        self._update_bounds()
        return frame

    def _record_base_resolution(self) -> None:
        if self.scores.empty:
            self.base_resolution = None
            return
        sample = str(self.scores["hex_id"].astype(str).iloc[0])
        h3 = _import_h3()
        self.base_resolution = int(h3.get_resolution(sample))

    def _update_bounds(self) -> None:
        if self.geometries.empty:
            self.bounds = None
            return
        lon = self.geometries["centroid_lon"].astype(float)
        lat = self.geometries["centroid_lat"].astype(float)
        self.bounds = (float(lon.min()), float(lat.min()), float(lon.max()), float(lat.max()))

    def frame_for_resolution(
        self, resolution: int, columns: Iterable[str] | None = None
    ) -> pd.DataFrame:
        columns = list(dict.fromkeys(columns or ["aucs"]))
        base_resolution = self.base_resolution or resolution
        if resolution >= base_resolution:
            required = ["hex_id", *columns]
            available = [col for col in required if col in self.scores.columns]
            return self.scores.loc[:, available].copy()
        cache_key: AggregationCacheKey = (resolution, tuple(sorted(columns)))
        cached = self._aggregation_cache.get(cache_key)
        if cached is not None:
            return cached.copy()
        frame = self.aggregate_by_resolution(resolution, columns=columns)
        self._aggregation_cache[cache_key] = frame
        return frame.copy()

    def ids_in_viewport(
        self,
        bounds: Bounds | None,
        *,
        resolution: int | None = None,
        buffer: float = 0.0,
    ) -> list[str]:
        if bounds is None or self.geometries.empty:
            return []
        lon_min, lat_min, lon_max, lat_max = bounds
        lon_min -= buffer
        lat_min -= buffer
        lon_max += buffer
        lat_max += buffer
        frame = self.geometries
        mask = (
            (frame["centroid_lon"] >= lon_min)
            & (frame["centroid_lon"] <= lon_max)
            & (frame["centroid_lat"] >= lat_min)
            & (frame["centroid_lat"] <= lat_max)
        )
        if resolution is not None and "resolution" in frame.columns:
            mask &= frame["resolution"] == resolution
        return frame.loc[mask, "hex_id"].astype(str).tolist()

    def apply_viewport(
        self, frame: pd.DataFrame, resolution: int, bounds: Bounds | None
    ) -> pd.DataFrame:
        if bounds is None or frame.empty:
            return frame
        candidates = self.ids_in_viewport(bounds, resolution=resolution, buffer=0.1)
        if not candidates:
            return frame
        subset = frame[frame["hex_id"].isin(candidates)]
        return subset if not subset.empty else frame

    def attach_geometries(self, frame: pd.DataFrame) -> pd.DataFrame:
        if frame.empty:
            return frame
        columns = ["hex_id", "centroid_lat", "centroid_lon"]
        if "geometry_wkt" in self.geometries.columns:
            columns.append("geometry_wkt")
        if "resolution" in self.geometries.columns:
            columns.append("resolution")
        merged = frame.merge(
            self.geometries[columns].drop_duplicates("hex_id"),
            on="hex_id",
            how="left",
        )
        return merged

    def rebuild_overlays(self, force: bool = False) -> None:
        """Public helper to recompute overlay GeoJSON payloads."""

        self._build_overlays(force=force)

    def get_overlay(self, key: str) -> FeatureCollection:
        """Return a GeoJSON overlay by key, ensuring an empty payload on miss."""

        payload = self.overlays.get(key)
        if payload is None:
            return empty_feature_collection()
        return payload

    def _build_overlays(self, force: bool = False) -> None:
        """Construct GeoJSON overlays for boundaries and external layers."""

        if not force and self._overlay_version == self._aggregation_version:
            return
        if self.scores.empty or self.geometries.empty:
            self.overlays.clear()
            self._overlay_version = self._aggregation_version
            return
        if shapely_wkt is None or unary_union is None or shapely_mapping is None:
            LOGGER.warning(
                "ui_overlays_shapely_missing",
                msg="Install shapely to enable boundary overlays",
            )
            self.overlays.clear()
            self._overlay_version = self._aggregation_version
            return

        assert shapely_wkt is not None
        assert unary_union is not None
        assert shapely_mapping is not None

        merged = self.scores.merge(
            self.geometries[["hex_id", "geometry_wkt"]],
            on="hex_id",
            how="left",
        )
        overlays: OverlayMap = {}
        for column, key in (("state", "states"), ("county", "counties"), ("metro", "metros")):
            if column not in merged.columns:
                continue
            features: list[GeoJSONFeature] = []
            for value, group in merged.groupby(column):
                if not value or group.empty:
                    continue
                shapes = [shapely_wkt.loads(wkt) for wkt in group["geometry_wkt"].dropna().unique()]
                if not shapes:
                    continue
                geometry = unary_union(shapes)
                if geometry.is_empty:
                    continue
                simplified = geometry.simplify(0.01, preserve_topology=True)
                feature_geometry = cast(GeoJSONGeometry, shapely_mapping(simplified))
                features.append(
                    {
                        "type": "Feature",
                        "geometry": feature_geometry,
                        "properties": {"label": str(value)},
                    }
                )
            if features:
                overlays[key] = {"type": "FeatureCollection", "features": features}

        overlays.update(self._load_external_overlays())
        self.overlays = overlays
        self._overlay_version = self._aggregation_version

    def _load_external_overlays(self) -> OverlayMap:
        """Load optional overlay GeoJSON files from the data directory."""

        result: OverlayMap = {}
        base = self.settings.data_path / "overlays"
        for name in ("transit_lines", "transit_stops", "parks"):
            path = base / f"{name}.geojson"
            if not path.exists():
                continue
            try:
                payload = json.loads(path.read_text())
            except json.JSONDecodeError as exc:
                LOGGER.warning("ui_overlay_invalid", name=name, error=str(exc))
                continue
            typed = self._coerce_feature_collection(payload)
            if typed is None:
                LOGGER.warning("ui_overlay_invalid", name=name, error="not a FeatureCollection")
                continue
            result[name] = typed
        return result

    @staticmethod
    def _coerce_feature_collection(payload: object) -> FeatureCollection | None:
        if not isinstance(payload, Mapping):
            return None
        if payload.get("type") != "FeatureCollection":
            return None
        features_obj = payload.get("features")
        if not isinstance(features_obj, Iterable):
            return None
        features: list[GeoJSONFeature] = []
        for feature in features_obj:
            if not isinstance(feature, Mapping):
                continue
            geometry = feature.get("geometry")
            properties = feature.get("properties", {})
            if not isinstance(geometry, Mapping) or not isinstance(properties, Mapping):
                continue
            geometry_mapping = cast(GeoJSONGeometry, {str(k): v for k, v in geometry.items()})
            property_mapping: dict[str, object] = {str(k): v for k, v in properties.items()}
            features.append(
                {
                    "type": "Feature",
                    "geometry": geometry_mapping,
                    "properties": property_mapping,
                }
            )
        return {"type": "FeatureCollection", "features": features}


__all__ = ["DataContext", "DatasetVersion"]
