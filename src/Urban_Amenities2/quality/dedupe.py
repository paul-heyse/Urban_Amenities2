from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
from numpy.typing import NDArray

EARTH_RADIUS_M = 6_371_000.0
LOGGER = logging.getLogger("aucs.quality.dedupe")


@dataclass(slots=True)
class BrandDedupeConfig:
    """Parameters for brand proximity deduplication."""

    distance_threshold_m: float = 500.0
    beta_per_km: float = 1.0
    brand_column: str = "brand"
    weight_column: str = "quality"
    category_column: str = "aucstype"
    lat_column: str = "lat"
    lon_column: str = "lon"


def apply_brand_dedupe(
    pois: pd.DataFrame,
    config: BrandDedupeConfig | None = None,
) -> tuple[pd.DataFrame, dict[str, float]]:
    if config is None:
        config = BrandDedupeConfig()
    if pois.empty:
        empty = pois.copy()
        empty["brand_penalty"] = pd.Series(dtype=float)
        empty["brand_weight"] = pd.Series(dtype=float)
        return empty, {"affected_ratio": 0.0}
    required = [config.brand_column, config.lat_column, config.lon_column]
    for column in required:
        if column not in pois.columns:
            raise ValueError(f"Column '{column}' required for brand deduplication")
    frame = pois.copy()
    base_weights = frame.get(
        config.weight_column,
        pd.Series(np.ones(len(frame), dtype=float), index=frame.index),
    ).astype(float)
    penalties = pd.Series(np.ones(len(frame), dtype=float), index=frame.index)
    affected_mask = pd.Series(np.zeros(len(frame), dtype=bool), index=frame.index)

    brand_series = frame[config.brand_column].fillna("").astype(str)
    valid_brands = brand_series.str.strip() != ""
    groups = frame[valid_brands].groupby(brand_series[valid_brands])

    for _brand, group in groups:
        if len(group) < 2:
            continue
        coords = group[[config.lat_column, config.lon_column]].to_numpy(dtype=float)
        distances = _pairwise_distance(coords)
        nearest = np.where(
            (distances > 0) & (distances <= config.distance_threshold_m),
            distances,
            np.nan,
        )
        penalty = np.nanmin(nearest, axis=1)
        penalty = np.where(np.isfinite(penalty), penalty, np.nan)
        factors = np.ones(len(group), dtype=float)
        close_mask = np.isfinite(penalty)
        if np.any(close_mask):
            d_km = penalty[close_mask] / 1000.0
            factors[close_mask] = 1.0 - np.exp(-config.beta_per_km * d_km)
            factors[close_mask] = np.clip(factors[close_mask], 0.0, 1.0)
            penalties.loc[group.index[close_mask]] = factors[close_mask]
            affected_mask.loc[group.index[close_mask]] = True

    frame["brand_penalty"] = penalties
    raw_weight = base_weights * penalties
    frame["brand_weight_raw"] = raw_weight

    # Preserve total weight per category by scaling back to the original sums.
    category_col = config.category_column
    if category_col in frame.columns:
        scaled = raw_weight.copy()
        for _category, group in frame.groupby(category_col):
            original_total = base_weights.loc[group.index].sum()
            dedup_total = raw_weight.loc[group.index].sum()
            if dedup_total <= 0 or original_total <= 0:
                continue
            scaled.loc[group.index] = raw_weight.loc[group.index] * (original_total / dedup_total)
        frame["brand_weight"] = scaled
    else:
        frame["brand_weight"] = raw_weight

    stats = {
        "affected_ratio": float(affected_mask.mean()),
        "avg_penalty": (
            float(frame.loc[affected_mask, "brand_penalty"].mean())
            if bool(affected_mask.any())
            else 0.0
        ),
    }
    LOGGER.info(
        "brand_dedupe affected_ratio=%.3f avg_penalty=%.3f count=%d",
        stats["affected_ratio"],
        stats["avg_penalty"],
        int(affected_mask.sum()),
    )
    return frame.drop(columns=["brand_weight_raw"]), stats


def _pairwise_distance(coords: NDArray[np.float64]) -> NDArray[np.float64]:
    if coords.size == 0:
        return np.zeros((0, 0), dtype=float)
    lat = np.radians(coords[:, 0])
    lon = np.radians(coords[:, 1])
    delta_lat = lat[:, None] - lat[None, :]
    delta_lon = lon[:, None] - lon[None, :]
    a = (
        np.sin(delta_lat / 2) ** 2
        + np.cos(lat)[:, None] * np.cos(lat)[None, :] * np.sin(delta_lon / 2) ** 2
    )
    distances = 2 * EARTH_RADIUS_M * np.arcsin(np.clip(np.sqrt(a), 0, 1))
    return np.asarray(distances, dtype=float)


__all__ = ["BrandDedupeConfig", "apply_brand_dedupe"]
