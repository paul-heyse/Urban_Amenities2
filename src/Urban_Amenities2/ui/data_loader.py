"""Utilities for loading and caching model output data for the UI."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Tuple

try:  # pragma: no cover - optional dependency handled gracefully
    from shapely import wkt as shapely_wkt
    from shapely.geometry import mapping as shapely_mapping
    from shapely.ops import unary_union
except ImportError:  # pragma: no cover - shapely is an optional runtime dependency
    shapely_wkt = None
    unary_union = None
    shapely_mapping = None

import pandas as pd

from ..logging_utils import get_logger
from .config import UISettings
from .hexes import HexGeometryCache, build_hex_index

LOGGER = get_logger("ui.data")

REQUIRED_COLUMNS = {
    "scores": {"hex_id", "aucs", "EA", "LCA", "MUHAA", "JEA", "MORR", "CTE", "SOU"},
    "metadata": {"hex_id", "state", "metro", "county"},
}


def _require_columns(frame: pd.DataFrame, required: Iterable[str]) -> None:
    missing = [column for column in required if column not in frame.columns]
    if missing:
        msg = f"DataFrame missing required columns: {missing}"
        raise KeyError(msg)


@dataclass(slots=True)
class DatasetVersion:
    identifier: str
    created_at: datetime
    path: Path

    @classmethod
    def from_path(cls, path: Path) -> "DatasetVersion":
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
    bounds: Tuple[float, float, float, float] | None = None
    _aggregation_cache: Dict[Tuple[int, Tuple[str, ...]], pd.DataFrame] = field(default_factory=dict)
    _aggregation_version: str | None = None
    overlays: Dict[str, dict] = field(default_factory=dict)
    _overlay_version: str | None = None

    @classmethod
    def from_settings(cls, settings: UISettings) -> "DataContext":
        context = cls(settings=settings)
        context.refresh()
        return context

    def refresh(self) -> None:
        """Reload parquet files if a newer version is available."""

        data_path = self.settings.data_path
        if not data_path.exists():
            LOGGER.warning("ui_data_path_missing", path=str(data_path))
            return

        parquet_files = sorted(data_path.glob("*.parquet"), key=lambda p: p.stat().st_mtime, reverse=True)
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
        hex_ids = self.scores["hex_id"].astype(str).unique()
        geometries = self.hex_cache.ensure_geometries(hex_ids)
        self.geometries = geometries
        self._update_bounds()

    def validate_geometries(self) -> None:
        if "hex_id" not in self.scores.columns:
            return
        self.hex_cache.validate(self.scores["hex_id"].astype(str))

    def _load_parquet(self, path: Path, columns: Optional[Iterable[str]] = None) -> pd.DataFrame:
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
        columns = list(columns) if columns else ["aucs", "EA", "LCA", "MUHAA", "JEA", "MORR", "CTE", "SOU"]
        summary = {}
        percentiles = [p / 100.0 for p in self.settings.summary_percentiles]
        for column in columns:
            if column not in self.scores.columns:
                continue
            series = self.scores[column]
            summary[column] = {
                "min": float(series.min()),
                "max": float(series.max()),
                "mean": float(series.mean()),
                **{f"p{int(p * 100)}": float(series.quantile(p)) for p in percentiles},
            }
        return pd.DataFrame(summary).T

    def export_geojson(self, path: Path, columns: Iterable[str] | None = None) -> Path:
        columns = list(columns) if columns else ["hex_id", "aucs"]
        frame = self.load_subset(columns + ["hex_id"])
        payload = self.to_geojson(frame)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload))
        return path

    def to_geojson(self, frame: pd.DataFrame) -> dict:
        geometries = self.geometries
        if geometries.empty:
            raise RuntimeError("Hex geometries not initialised")
        merged = frame.merge(geometries, on="hex_id", how="left")
        features = []
        for record in merged.to_dict("records"):
            geometry = json.loads(record.pop("geometry"))
            features.append({"type": "Feature", "geometry": geometry, "properties": record})
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

    def get_hex_index(self, resolution: int) -> Mapping[str, List[str]]:
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
        h3 = __import__("h3")
        subset["parent_hex"] = [
            h3.cell_to_parent(hex_id, resolution) for hex_id in subset["hex_id"]
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
        h3 = __import__("h3")
        self.base_resolution = h3.get_resolution(sample)

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
        cache_key = (resolution, tuple(sorted(columns)))
        cached = self._aggregation_cache.get(cache_key)
        if cached is not None:
            return cached.copy()
        frame = self.aggregate_by_resolution(resolution, columns=columns)
        self._aggregation_cache[cache_key] = frame
        return frame.copy()

    def ids_in_viewport(
        self,
        bounds: Tuple[float, float, float, float] | None,
        *,
        resolution: int | None = None,
        buffer: float = 0.0,
    ) -> List[str]:
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
        self, frame: pd.DataFrame, resolution: int, bounds: Tuple[float, float, float, float] | None
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

    def get_overlay(self, key: str) -> dict:
        """Return a GeoJSON overlay by key, ensuring an empty payload on miss."""

        payload = self.overlays.get(key, {})
        if not payload:
            return {"type": "FeatureCollection", "features": []}
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

        merged = self.scores.merge(
            self.geometries[["hex_id", "geometry_wkt"]],
            on="hex_id",
            how="left",
        )
        overlays: Dict[str, dict] = {}
        for column, key in (("state", "states"), ("county", "counties"), ("metro", "metros")):
            if column not in merged.columns:
                continue
            features = []
            for value, group in merged.groupby(column):
                if not value or group.empty:
                    continue
                shapes = [
                    shapely_wkt.loads(wkt)
                    for wkt in group["geometry_wkt"].dropna().unique()
                ]
                if not shapes:
                    continue
                geometry = unary_union(shapes)
                if geometry.is_empty:
                    continue
                simplified = geometry.simplify(0.01, preserve_topology=True)
                features.append(
                    {
                        "type": "Feature",
                        "geometry": shapely_mapping(simplified),
                        "properties": {"label": value},
                    }
                )
            if features:
                overlays[key] = {"type": "FeatureCollection", "features": features}

        overlays.update(self._load_external_overlays())
        self.overlays = overlays
        self._overlay_version = self._aggregation_version

    def _load_external_overlays(self) -> Dict[str, dict]:
        """Load optional overlay GeoJSON files from the data directory."""

        result: Dict[str, dict] = {}
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
            result[name] = payload
        return result


__all__ = ["DataContext", "DatasetVersion"]
