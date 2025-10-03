from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

if TYPE_CHECKING:  # pragma: no cover - import for type checking only
    from ..config.params import QualityConfig


HOURS_BONUS_MAP: dict[str, float] = {
    "24_7": 0.20,
    "extended": 0.10,
    "standard": 0.0,
    "limited": -0.10,
}

_COMPONENTS = ("size", "popularity", "brand", "heritage")


@dataclass(slots=True)
class QualityScoringConfig:
    """Runtime configuration for computing amenity quality scores."""

    component_weights: Mapping[str, float]
    z_clip_abs: float = 3.0
    opening_hours_bonus_xi: float = 1.0
    category_defaults: Mapping[str, Mapping[str, float]] | None = None
    hours_defaults: Mapping[str, str] | None = None

    def normalised_weights(self) -> dict[str, float]:
        total = float(sum(self.component_weights.get(name, 0.0) for name in _COMPONENTS))
        if total <= 0:
            raise ValueError("Quality component weights must sum to a positive value")
        return {name: float(self.component_weights.get(name, 0.0)) / total for name in _COMPONENTS}


class QualityScorer:
    """Compute quality scores (Q_a) for points of interest."""

    def __init__(self, config: QualityScoringConfig):
        self.config = config
        self.weights = config.normalised_weights()

    def score(self, pois: pd.DataFrame, category_col: str = "aucstype") -> pd.DataFrame:
        if pois.empty:
            empty = pois.copy()
            empty["quality"] = pd.Series(dtype=float)
            for column in (
                "quality_base",
                "quality_size",
                "quality_popularity",
                "quality_brand",
                "quality_heritage",
                "quality_hours_bonus",
            ):
                empty[column] = pd.Series(dtype=float)
            empty["quality_hours_category"] = pd.Series(dtype=str)
            empty["quality_components"] = pd.Series(dtype=object)
            return empty
        if category_col not in pois.columns:
            raise ValueError(f"{category_col} column is required to compute quality scores")

        frame = pois.copy()
        categories = frame[category_col].fillna("unknown")

        size_metric = _compute_size_metric(frame)
        popularity_metric = _compute_popularity_metric(frame)
        heritage_metric = _compute_heritage_metric(frame)
        brand_metric = _compute_brand_metric(frame)

        size_score = _score_component(
            size_metric,
            categories,
            "size",
            self.config,
        )
        popularity_score = _score_component(
            popularity_metric,
            categories,
            "popularity",
            self.config,
        )
        heritage_score = _score_component(
            heritage_metric,
            categories,
            "heritage",
            self.config,
            binary=True,
        )
        brand_score = _score_component(
            brand_metric,
            categories,
            "brand",
            self.config,
            binary=True,
        )

        component_scores = pd.DataFrame(
            {
                "quality_size": size_score,
                "quality_popularity": popularity_score,
                "quality_brand": brand_score,
                "quality_heritage": heritage_score,
            },
            index=frame.index,
        )
        base_quality = sum(component_scores[f"quality_{name}"] * self.weights[name] for name in _COMPONENTS)

        hours_category = _classify_hours(frame, categories, self.config.hours_defaults)
        bonus = np.array([HOURS_BONUS_MAP.get(value, 0.0) for value in hours_category])
        bonus_scaled = 1.0 + self.config.opening_hours_bonus_xi * bonus
        quality_total = base_quality.to_numpy(dtype=float) * bonus_scaled
        quality_total = np.clip(quality_total, 0.0, 100.0)

        component_scores["quality_base"] = base_quality
        component_scores["quality_hours_category"] = hours_category
        component_scores["quality_hours_bonus"] = bonus
        component_scores["quality"] = quality_total
        component_scores["quality_components"] = [
            {
                "size": float(component_scores.loc[idx, "quality_size"]),
                "popularity": float(component_scores.loc[idx, "quality_popularity"]),
                "brand": float(component_scores.loc[idx, "quality_brand"]),
                "heritage": float(component_scores.loc[idx, "quality_heritage"]),
            }
            for idx in component_scores.index
        ]

        if component_scores[["quality"]].isna().values.any():
            raise ValueError("Computed quality scores contain NaN values")

        return frame.join(component_scores)


def summarize_quality(frame: pd.DataFrame, category_col: str = "aucstype") -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(
            columns=[
                category_col,
                "count",
                "mean_quality",
                "median_quality",
                "quality_std",
                "share_24_7",
                "share_extended",
            ]
        )
    if "quality" not in frame.columns:
        raise ValueError("Frame must contain a 'quality' column to summarize")
    grouped = frame.groupby(category_col)
    summary = grouped["quality"].agg(["count", "mean", "median", "std"]).reset_index()
    summary = summary.rename(
        columns={
            "mean": "mean_quality",
            "median": "median_quality",
            "std": "quality_std",
        }
    )
    summary["quality_std"] = summary["quality_std"].fillna(0.0)
    hours = frame.get("quality_hours_category")
    if hours is not None:
        summary = summary.merge(
            (
                frame.assign(_hours=hours)
                .groupby([category_col, "_hours"])["poi_id" if "poi_id" in frame.columns else category_col]
                .count()
                .unstack(fill_value=0)
                .rename(columns=lambda value: f"count_{value}")
            ),
            on=category_col,
            how="left",
        )
        for column in ("count_24_7", "count_extended"):
            if column not in summary.columns:
                summary[column] = 0
        summary["share_24_7"] = summary["count_24_7"].div(summary["count"].where(summary["count"] > 0, np.nan)).fillna(0.0)
        summary["share_extended"] = summary["count_extended"].div(summary["count"].where(summary["count"] > 0, np.nan)).fillna(0.0)
        summary = summary.drop(columns=[col for col in summary.columns if col.startswith("count_")])
    else:
        summary["share_24_7"] = 0.0
        summary["share_extended"] = 0.0
    return summary


def build_scoring_config(
    config: QualityConfig,
    category_defaults: Mapping[str, Mapping[str, float]] | None = None,
    hours_defaults: Mapping[str, str] | None = None,
) -> QualityScoringConfig:
    return QualityScoringConfig(
        component_weights=config.component_weights,
        z_clip_abs=config.z_clip_abs,
        opening_hours_bonus_xi=config.opening_hours_bonus_xi,
        category_defaults=category_defaults,
        hours_defaults=hours_defaults,
    )


def _compute_size_metric(frame: pd.DataFrame) -> pd.Series:
    candidates = []
    for column in ("square_footage", "size_sqft", "floor_area", "seating_capacity", "collection_size", "capacity"):
        if column in frame.columns:
            candidates.append(pd.to_numeric(frame[column], errors="coerce"))
    if not candidates:
        return pd.Series(0.0, index=frame.index)
    values = pd.concat(candidates, axis=1)
    metric = np.nanmax(values.to_numpy(dtype=float), axis=1)
    metric = np.where(np.isfinite(metric), metric, 0.0)
    return pd.Series(np.log1p(metric), index=frame.index)


def _compute_popularity_metric(frame: pd.DataFrame) -> pd.Series:
    candidates = []
    for column in ("median_views", "pageviews", "weekly_pageviews", "sitelinks_count", "popularity_z"):
        if column in frame.columns:
            series = pd.to_numeric(frame[column], errors="coerce")
            if column == "popularity_z":
                candidates.append(series)
            else:
                candidates.append(np.log1p(series))
    if not candidates:
        return pd.Series(0.0, index=frame.index)
    values = pd.concat(candidates, axis=1)
    return values.mean(axis=1, skipna=True).fillna(0.0)


def _compute_heritage_metric(frame: pd.DataFrame) -> pd.Series:
    heritage = np.zeros(len(frame), dtype=float)
    if "heritage_status" in frame.columns:
        heritage += frame["heritage_status"].notna().astype(float) * 2.0
        heritage += frame["heritage_status"].astype(str).str.contains("unesco", case=False, na=False).astype(float)
    for column in ("is_museum", "is_library", "is_historic"):
        if column in frame.columns:
            heritage += frame[column].fillna(0).astype(float)
    return pd.Series(heritage, index=frame.index)


def _compute_brand_metric(frame: pd.DataFrame) -> pd.Series:
    base = np.zeros(len(frame), dtype=float)
    brand_col = frame.get("brand")
    if brand_col is not None:
        base += brand_col.fillna("").astype(str).str.len().clip(upper=80) / 80.0
    for column in ("brand_wd", "wikidata_brand", "brand_qid"):
        if column in frame.columns:
            base += frame[column].notna().astype(float) * 1.5
    if "is_chain" in frame.columns:
        base += frame["is_chain"].fillna(0).astype(float) * 2.0
    if "chain_size" in frame.columns:
        base += np.log1p(pd.to_numeric(frame["chain_size"], errors="coerce").fillna(0.0))
    return pd.Series(base, index=frame.index)


def _score_component(
    values: pd.Series,
    categories: pd.Series,
    component: str,
    config: QualityScoringConfig,
    *,
    binary: bool = False,
) -> pd.Series:
    defaults = config.category_defaults or {}
    scored = pd.Series(np.zeros(len(values), dtype=float), index=values.index)
    for category, group in values.groupby(categories):
        default = defaults.get(category, {}).get(component) if isinstance(defaults, Mapping) else None
        if default is not None:
            filled = group.fillna(float(default))
        else:
            filled = group.fillna(group.median())
        if filled.isna().all():
            scores = pd.Series(np.full(len(group), 50.0, dtype=float), index=group.index)
        elif binary:
            clipped = filled.clip(lower=0.0, upper=1.0)
            scores = pd.Series(clipped * 100.0, index=group.index)
        else:
            mean = float(filled.mean())
            std = float(filled.std(ddof=0))
            if not np.isfinite(std) or std == 0.0:
                scores = pd.Series(np.full(len(group), 50.0, dtype=float), index=group.index)
            else:
                z = (filled - mean) / std
                z = z.clip(-config.z_clip_abs, config.z_clip_abs)
                rescaled = (z + config.z_clip_abs) / (2 * config.z_clip_abs)
                scores = pd.Series(rescaled * 100.0, index=group.index)
        scored.loc[group.index] = scores
    return scored.fillna(0.0)


def _classify_hours(
    frame: pd.DataFrame,
    categories: pd.Series,
    defaults: Mapping[str, str] | None,
) -> pd.Series:
    if "opening_hours_type" in frame.columns:
        series = frame["opening_hours_type"].fillna("").astype(str)
        mapped = series.map(
            {
                "24/7": "24_7",
                "24_7": "24_7",
                "extended": "extended",
                "standard": "standard",
                "limited": "limited",
            }
        )
    else:
        mapped = pd.Series([None] * len(frame), index=frame.index, dtype=object)

    numeric_hours = None
    for column in ("hours_per_day", "opening_hours_hours_per_day"):
        if column in frame.columns:
            numeric_hours = pd.to_numeric(frame[column], errors="coerce")
            break
    if numeric_hours is not None:
        mapped = mapped.combine_first(numeric_hours.map(_classify_numeric_hours))

    if "opening_hours" in frame.columns:
        parsed = frame["opening_hours"].astype(str).apply(_parse_hours_string)
        mapped = mapped.combine_first(parsed.map(_classify_numeric_hours))

    defaults = defaults or {}
    result: list[str] = []
    for idx, category in categories.items():
        value = mapped.loc[idx]
        if value:
            result.append(value)
            continue
        fallback = defaults.get(category) or defaults.get("default")
        result.append(fallback or "standard")
    return pd.Series(result, index=frame.index, dtype=str)


def _classify_numeric_hours(hours: float | None) -> str | None:
    if hours is None or not np.isfinite(hours):
        return None
    if hours >= 23.5:
        return "24_7"
    if hours > 12:
        return "extended"
    if hours >= 6:
        return "standard"
    return "limited"


def _parse_hours_string(value: str) -> float | None:
    lower = value.lower().strip()
    if not lower or lower in {"nan", "none"}:
        return None
    if "24/7" in lower or "24-7" in lower or "24 hours" in lower:
        return 24.0
    import re

    matches = re.findall(r"(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})", lower)
    if not matches:
        return None
    durations: list[float] = []
    for start_h, start_m, end_h, end_m in matches:
        start_minutes = int(start_h) * 60 + int(start_m)
        end_minutes = int(end_h) * 60 + int(end_m)
        if end_minutes < start_minutes:
            end_minutes += 24 * 60
        durations.append((end_minutes - start_minutes) / 60.0)
    if not durations:
        return None
    return float(np.mean(durations))


__all__ = [
    "HOURS_BONUS_MAP",
    "QualityScorer",
    "QualityScoringConfig",
    "build_scoring_config",
    "summarize_quality",
]
