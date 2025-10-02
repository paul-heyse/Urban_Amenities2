"""Utilities for loading and caching model output data for the UI."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional

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
        self._prepare_geometries()
        self.validate_geometries()

    def _prepare_geometries(self) -> None:
        if "hex_id" not in self.scores.columns:
            return
        hex_ids = self.scores["hex_id"].astype(str).unique()
        geometries = self.hex_cache.ensure_geometries(hex_ids)
        self.geometries = geometries

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
        subset = self.scores[list(columns)].copy()
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
        index = self.get_hex_index(resolution)
        if not index:
            return pd.DataFrame()
        columns = list(dict.fromkeys(columns or ["aucs"]))
        records: list[dict[str, object]] = []
        for parent, children in index.items():
            subset = self.scores[self.scores["hex_id"].isin(children)]
            if subset.empty:
                continue
            record = {"hex_id": parent, "count": int(len(subset))}
            for column in columns:
                if column in subset:
                    record[column] = float(subset[column].mean())
            records.append(record)
        frame = pd.DataFrame.from_records(records)
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
        return frame


__all__ = ["DataContext", "DatasetVersion"]
