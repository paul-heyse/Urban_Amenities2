"""Utilities for loading and caching model output data for the UI."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from importlib import import_module
from pathlib import Path
from typing import Any, cast

import pandas as pd

from ..logging_utils import get_logger
from .config import UISettings
from .export import build_feature_collection
from .export_types import GeoJSONFeature, GeoJSONFeatureCollection, GeoJSONGeometry, TabularData
from .hexes import HexGeometryCache, build_hex_index

LOGGER = get_logger("ui.data")

REQUIRED_COLUMNS: dict[str, set[str]] = {
    "scores": {"hex_id", "aucs", "EA", "LCA", "MUHAA", "JEA", "MORR", "CTE", "SOU"},
    "metadata": {"hex_id", "state", "metro", "county"},
}


def _require_columns(frame: TabularData, required: Iterable[str]) -> None:
    missing = [column for column in required if column not in frame.columns]
    if missing:
        msg = f"DataFrame missing required columns: {missing}"
        raise KeyError(msg)


def _import_h3() -> Any:
    return import_module("h3")


def _import_shapely_modules() -> (
    tuple[Any, Callable[[object], dict[str, object]], Callable[[Sequence[object]], object]]
):
    shapely_wkt = import_module("shapely.wkt")
    shapely_geometry = import_module("shapely.geometry")
    shapely_ops = import_module("shapely.ops")
    return shapely_wkt, shapely_geometry.mapping, shapely_ops.unary_union


@dataclass(slots=True)
class DatasetVersion:
    identifier: str
    created_at: datetime
    path: Path

    @classmethod
    def from_path(cls, path: Path, base_path: Path | None = None) -> DatasetVersion:
        stat = path.stat()
        identifier = cls._derive_identifier(path, base_path)
        created_at = datetime.fromtimestamp(stat.st_mtime)
        return cls(identifier=identifier, created_at=created_at, path=path)

    @staticmethod
    def _derive_identifier(path: Path, base_path: Path | None) -> str:
        stem = path.stem
        if stem.endswith("_scores"):
            stem = stem[: -len("_scores")]
        if base_path is not None and (not stem or stem == "scores"):
            try:
                resolved_base = base_path.resolve()
                resolved_parent = path.parent.resolve()
            except FileNotFoundError:
                resolved_base = base_path
                resolved_parent = path.parent
            if resolved_parent != resolved_base:
                stem = resolved_parent.name
        return stem

    def matching_metadata_candidates(self) -> list[Path]:
        base = self.path.parent
        candidates: list[Path] = []
        if self.identifier:
            candidates.append(base / f"{self.identifier}_metadata.parquet")
        candidates.append(base / "metadata.parquet")
        return candidates


@dataclass(slots=True)
class DataContext:
    """Holds loaded datasets and derived aggregates for the UI."""

    settings: UISettings
    scores: TabularData = field(default_factory=pd.DataFrame)
    metadata: TabularData = field(default_factory=pd.DataFrame)
    geometries: TabularData = field(default_factory=pd.DataFrame)
    version: DatasetVersion | None = None
    hex_cache: HexGeometryCache = field(default_factory=HexGeometryCache)
    base_resolution: int | None = None
    bounds: tuple[float, float, float, float] | None = None
    _aggregation_cache: dict[tuple[int, tuple[str, ...]], TabularData] = field(default_factory=dict)
    _aggregation_version: str | None = None
    overlays: dict[str, GeoJSONFeatureCollection] = field(default_factory=dict)
    _overlay_version: str | None = None
    _available_versions: list[DatasetVersion] = field(default_factory=list)

    @classmethod
    def from_settings(cls, settings: UISettings) -> DataContext:
        context = cls(settings=settings)
        context.refresh()
        return context

    def refresh(
        self,
        version: str | DatasetVersion | None = None,
        *,
        force: bool = False,
    ) -> None:
        data_path = self.settings.data_path
        if not data_path.exists():
            LOGGER.warning("ui_data_path_missing", path=str(data_path))
            self._available_versions = []
            return
        versions = self._discover_versions(data_path)
        self._available_versions = versions
        if not versions:
            LOGGER.warning("ui_scores_missing", path=str(data_path))
            self.version = None
            self.scores = pd.DataFrame()
            self.metadata = pd.DataFrame()
            self.geometries = pd.DataFrame()
            self.overlays.clear()
            self._aggregation_cache.clear()
            self._aggregation_version = None
            self._overlay_version = None
            self.base_resolution = None
            self.bounds = None
            return

        target = self._select_version(version, versions)
        if target is None:
            LOGGER.warning(
                "ui_dataset_version_not_found",
                requested=str(version),
                available=[candidate.identifier for candidate in versions],
            )
            return
        if not force and self.version is not None and self.version.identifier == target.identifier:
            return

        LOGGER.info("ui_loading_dataset", version=target.identifier)
        scores = self._load_parquet(target.path, columns=None)
        _require_columns(scores, REQUIRED_COLUMNS["scores"])

        metadata = self._load_metadata(target)
        if len(metadata):
            scores = scores.merge(metadata, on="hex_id", how="left")

        self.scores = scores
        self.metadata = metadata
        self.version = target
        self._aggregation_cache.clear()
        self._aggregation_version = target.identifier
        self._prepare_geometries()
        self.validate_geometries()
        self._record_base_resolution()
        self._build_overlays(force=True, version=target)

    def available_versions(self) -> list[DatasetVersion]:
        return list(self._available_versions)

    def load_version(self, identifier: str) -> bool:
        target = self._select_version(identifier, self._available_versions)
        if target is None:
            LOGGER.warning(
                "ui_dataset_version_not_found",
                requested=identifier,
                available=[candidate.identifier for candidate in self._available_versions],
            )
            return False
        self.refresh(target, force=True)
        return self.version is not None and self.version.identifier == target.identifier

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

    def _load_parquet(self, path: Path, columns: Iterable[str] | None = None) -> TabularData:
        frame = pd.read_parquet(path, columns=list(columns) if columns else None)
        if "hex_id" in frame.columns:
            frame["hex_id"] = frame["hex_id"].astype("category")
        return cast(TabularData, frame)

    def load_subset(self, columns: Iterable[str]) -> TabularData:
        if len(self.scores) == 0:
            return self.scores
        unique_columns = list(dict.fromkeys(columns))
        subset = self.scores[unique_columns].copy()
        return cast(TabularData, subset)

    def filter_scores(
        self,
        *,
        state: Iterable[str] | None = None,
        metro: Iterable[str] | None = None,
        county: Iterable[str] | None = None,
        score_range: tuple[float, float] | None = None,
    ) -> TabularData:
        frame = self.scores
        if len(frame) == 0 or len(self.metadata) == 0:
            return frame
        mask = pd.Series(True, index=frame.index)
        if state:
            mask &= frame["state"].isin(state)
        if metro:
            mask &= frame["metro"].isin(metro)
        if county:
            mask &= frame["county"].isin(county)
        if score_range:
            low, high = score_range
            mask &= frame["aucs"].between(low, high)
        return cast(TabularData, frame[mask])

    def summarise(self, columns: Iterable[str] | None = None) -> TabularData:
        if len(self.scores) == 0:
            return cast(TabularData, pd.DataFrame())
        columns = (
            list(columns)
            if columns
            else ["aucs", "EA", "LCA", "MUHAA", "JEA", "MORR", "CTE", "SOU"]
        )
        summary: dict[str, dict[str, float]] = {}
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
            summary[column] = stats
        return cast(TabularData, pd.DataFrame(summary).T)

    def export_geojson(self, path: Path, columns: Iterable[str] | None = None) -> Path:
        columns = list(columns) if columns else ["hex_id", "aucs"]
        frame = self.load_subset(columns + ["hex_id"])
        collection = build_feature_collection(frame)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(collection))
        return path

    def to_geojson(self, frame: TabularData) -> GeoJSONFeatureCollection:
        geometries = self.geometries
        if len(geometries) == 0:
            raise RuntimeError("Hex geometries not initialised")
        merged = frame.merge(geometries, on="hex_id", how="left")
        return build_feature_collection(cast(TabularData, merged))

    def export_csv(self, path: Path, columns: Iterable[str] | None = None) -> Path:
        columns = list(columns) if columns else ["hex_id", "aucs", "EA", "LCA"]
        frame = self.load_subset(columns)
        path.parent.mkdir(parents=True, exist_ok=True)
        cast(TabularData, frame).to_csv(str(path), index=False)
        return path

    def export_shapefile(self, path: Path, columns: Iterable[str] | None = None) -> Path:
        geopandas = import_module("geopandas")
        columns = list(columns) if columns else ["hex_id", "aucs"]
        frame = self.load_subset(columns + ["hex_id"])
        geometries = self.geometries
        if len(geometries) == 0:
            raise RuntimeError("Hex geometries not initialised")
        merged = frame.merge(geometries, on="hex_id", how="left")
        geo_frame = geopandas.GeoDataFrame(
            merged.drop(columns=["geometry"]),
            geometry=geopandas.GeoSeries.from_wkt(merged["geometry_wkt"]),
            crs="EPSG:4326",
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        geo_frame.to_file(str(path))
        return path

    def get_hex_index(self, resolution: int) -> Mapping[str, list[str]]:
        if len(self.geometries) == 0:
            return {}
        return build_hex_index(self.geometries, resolution)

    def aggregate_by_resolution(
        self, resolution: int, columns: Iterable[str] | None = None
    ) -> TabularData:
        if len(self.scores) == 0:
            return cast(TabularData, pd.DataFrame())
        columns = list(dict.fromkeys(columns or ["aucs"]))
        subset_columns = ["hex_id", *columns]
        subset = self.scores[subset_columns].copy()
        if len(subset) == 0:
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
        if len(frame) == 0:
            return cast(TabularData, frame)
        new_geoms = self.hex_cache.ensure_geometries(frame["hex_id"].astype(str).tolist())
        if len(self.geometries) == 0:
            self.geometries = new_geoms
        else:
            self.geometries = cast(
                TabularData,
                pd.concat([self.geometries, new_geoms])
                .drop_duplicates(subset=["hex_id"], keep="last")
                .reset_index(drop=True),
            )
        self._update_bounds()
        return cast(TabularData, frame)

    def _record_base_resolution(self) -> None:
        if len(self.scores) == 0:
            self.base_resolution = None
            return
        sample = str(self.scores["hex_id"].astype(str).iloc[0])
        h3 = _import_h3()
        self.base_resolution = int(h3.get_resolution(sample))

    def _update_bounds(self) -> None:
        if len(self.geometries) == 0:
            self.bounds = None
            return
        lon = self.geometries["centroid_lon"].astype(float)
        lat = self.geometries["centroid_lat"].astype(float)
        self.bounds = (float(lon.min()), float(lat.min()), float(lon.max()), float(lat.max()))

    def frame_for_resolution(
        self, resolution: int, columns: Iterable[str] | None = None
    ) -> TabularData:
        columns = list(dict.fromkeys(columns or ["aucs"]))
        base_resolution = self.base_resolution or resolution
        if resolution >= base_resolution:
            required = ["hex_id", *columns]
            available = [col for col in required if col in self.scores.columns]
            return cast(TabularData, self.scores.loc[:, available].copy())
        cache_key = (resolution, tuple(sorted(columns)))
        cached = self._aggregation_cache.get(cache_key)
        if cached is not None:
            return cast(TabularData, cached.copy())
        frame = self.aggregate_by_resolution(resolution, columns=columns)
        self._aggregation_cache[cache_key] = cast(TabularData, frame)
        return cast(TabularData, frame.copy())

    def ids_in_viewport(
        self,
        bounds: tuple[float, float, float, float] | None,
        *,
        resolution: int | None = None,
        buffer: float = 0.0,
    ) -> list[str]:
        if bounds is None or len(self.geometries) == 0:
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
        return [str(value) for value in frame.loc[mask, "hex_id"].astype(str).tolist()]

    def apply_viewport(
        self,
        frame: TabularData,
        resolution: int,
        bounds: tuple[float, float, float, float] | None,
    ) -> TabularData:
        if bounds is None or len(frame) == 0:
            return frame
        candidates = self.ids_in_viewport(bounds, resolution=resolution, buffer=0.1)
        if not candidates:
            return frame
        subset = frame[frame["hex_id"].isin(candidates)]
        return cast(TabularData, subset if len(subset) else frame)

    def attach_geometries(self, frame: TabularData) -> TabularData:
        if len(frame) == 0:
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
        return cast(TabularData, merged)

    def rebuild_overlays(self, force: bool = False) -> None:
        self._build_overlays(force=force, version=self.version)

    def get_overlay(self, key: str) -> GeoJSONFeatureCollection:
        payload = self.overlays.get(key)
        if payload:
            return payload
        return {"type": "FeatureCollection", "features": []}

    def _build_overlays(
        self,
        *,
        force: bool = False,
        version: DatasetVersion | None = None,
    ) -> None:
        if not force and self._overlay_version == self._aggregation_version:
            return
        if len(self.scores) == 0 or len(self.geometries) == 0:
            self.overlays.clear()
            self._overlay_version = self._aggregation_version
            return
        try:
            shapely_wkt, shapely_mapping, unary_union = _import_shapely_modules()
        except ImportError:
            LOGGER.warning(
                "ui_overlays_shapely_missing",
                msg="Install shapely to enable boundary overlays",
            )
            self.overlays.clear()
            self._overlay_version = self._aggregation_version
            return

        merged = self.scores.merge(
            self.geometries[["hex_id", "geometry_wkt"]],
            on="hex_id",
            how="left",
        )
        overlays: dict[str, GeoJSONFeatureCollection] = {}
        for column, key in (("state", "states"), ("county", "counties"), ("metro", "metros")):
            if column not in merged.columns:
                continue
            features: list[GeoJSONFeature] = []
            for value, group in merged.groupby(column):
                if not value or len(group) == 0:
                    continue
                shapes = [shapely_wkt.loads(wkt) for wkt in group["geometry_wkt"].dropna().unique()]
                if not shapes:
                    continue
                geometry = unary_union(shapes)
                if geometry.is_empty:
                    continue
                simplified = geometry.simplify(0.01, preserve_topology=True)
                geometry_payload = cast(GeoJSONGeometry, shapely_mapping(simplified))
                features.append(
                    {
                        "type": "Feature",
                        "geometry": geometry_payload,
                        "properties": {"label": value},
                    }
                )
            if features:
                overlays[key] = {"type": "FeatureCollection", "features": features}

        overlays.update(self._load_external_overlays(version))
        self.overlays = overlays
        self._overlay_version = self._aggregation_version

    def _load_external_overlays(
        self, version: DatasetVersion | None = None
    ) -> dict[str, GeoJSONFeatureCollection]:
        result: dict[str, GeoJSONFeatureCollection] = {}
        search_roots: list[Path] = []
        if version is not None:
            search_roots.append(version.path.parent / "overlays")
        search_roots.append(self.settings.data_path / "overlays")

        seen_roots: set[Path] = set()
        for base in search_roots:
            if base in seen_roots or not base.exists():
                continue
            seen_roots.add(base)
            for name in ("transit_lines", "transit_stops", "parks"):
                if name in result:
                    continue
                path = base / f"{name}.geojson"
                if not path.exists():
                    continue
                try:
                    payload = json.loads(path.read_text())
                except json.JSONDecodeError as exc:
                    LOGGER.warning("ui_overlay_invalid", name=name, error=str(exc))
                    continue
                if payload.get("type") != "FeatureCollection":
                    LOGGER.warning("ui_overlay_invalid_type", name=name)
                    continue
                features = payload.get("features")
                if not isinstance(features, list):
                    LOGGER.warning("ui_overlay_invalid_features", name=name)
                    continue
                typed_features: list[GeoJSONFeature] = []
                for feature in features:
                    if isinstance(feature, dict):
                        typed_features.append(cast(GeoJSONFeature, feature))
                result[name] = {
                    "type": "FeatureCollection",
                    "features": typed_features,
                }
        return result

    def _discover_versions(self, data_path: Path) -> list[DatasetVersion]:
        candidates: list[DatasetVersion] = []
        parquet_files = sorted(
            data_path.glob("*.parquet"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for path in parquet_files:
            if not self._is_score_file(path):
                continue
            candidates.append(DatasetVersion.from_path(path, data_path))
        for child in data_path.iterdir():
            if not child.is_dir():
                continue
            for nested in child.glob("*.parquet"):
                if not self._is_score_file(nested):
                    continue
                candidates.append(DatasetVersion.from_path(nested, data_path))
        unique: dict[Path, DatasetVersion] = {}
        for candidate in candidates:
            try:
                key = candidate.path.resolve()
            except FileNotFoundError:
                key = candidate.path
            unique[key] = candidate
        ordered = sorted(unique.values(), key=lambda item: item.created_at, reverse=True)
        return ordered

    @staticmethod
    def _is_score_file(path: Path) -> bool:
        name = path.name
        if name == "metadata.parquet":
            return False
        stem = path.stem
        return stem.endswith("_scores") or stem == "scores"

    def _select_version(
        self,
        requested: str | DatasetVersion | None,
        versions: Sequence[DatasetVersion],
    ) -> DatasetVersion | None:
        if requested is None:
            return versions[0]
        if isinstance(requested, DatasetVersion):
            return requested
        for version in versions:
            if version.identifier == requested or version.path.name == requested:
                return version
        return None

    def _load_metadata(self, version: DatasetVersion) -> TabularData:
        tried: set[Path] = set()
        for candidate in version.matching_metadata_candidates():
            if not candidate.exists():
                continue
            tried.add(candidate)
            frame = self._load_parquet(candidate)
            try:
                _require_columns(frame, REQUIRED_COLUMNS["metadata"])
            except KeyError as exc:
                LOGGER.warning(
                    "ui_metadata_invalid",
                    error=str(exc),
                    path=str(candidate),
                )
                continue
            return frame
        fallback = self.settings.data_path / "metadata.parquet"
        if fallback.exists() and fallback not in tried:
            frame = self._load_parquet(fallback)
            try:
                _require_columns(frame, REQUIRED_COLUMNS["metadata"])
            except KeyError as exc:
                LOGGER.warning(
                    "ui_metadata_invalid",
                    error=str(exc),
                    path=str(fallback),
                )
            else:
                return frame
        return cast(TabularData, pd.DataFrame())


__all__ = ["DataContext", "DatasetVersion"]
