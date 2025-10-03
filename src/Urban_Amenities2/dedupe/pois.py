from __future__ import annotations

from dataclasses import dataclass
from math import exp

import numpy as np
from numpy.typing import NDArray
import pandas as pd
from rapidfuzz import fuzz

from ..hex.core import latlon_to_hex

EARTH_RADIUS_M = 6_371_000.0


@dataclass
class DedupeConfig:
    brand_distance_m: float = 50.0
    name_distance_m: float = 25.0
    name_similarity: float = 0.85
    beta_per_km: float = 3.0
    distance_overrides: dict[str, float] | None = None


def ensure_hex_index(
    frame: pd.DataFrame,
    lat_col: str = "lat",
    lon_col: str = "lon",
    hex_col: str = "hex_id",
) -> pd.DataFrame:
    if hex_col in frame.columns:
        return frame
    assigned = frame.copy()
    assigned[hex_col] = [
        latlon_to_hex(float(row[lat_col]), float(row[lon_col])) for _, row in frame.iterrows()
    ]
    return assigned


def deduplicate_pois(
    frame: pd.DataFrame,
    config: DedupeConfig | None = None,
    brand_col: str = "brand",
    name_col: str = "name",
    hex_col: str = "hex_id",
    lat_col: str = "lat",
    lon_col: str = "lon",
    category_col: str = "aucstype",
    confidence_col: str = "confidence",
) -> pd.DataFrame:
    if config is None:
        config = DedupeConfig()
    frame = ensure_hex_index(frame, lat_col=lat_col, lon_col=lon_col, hex_col=hex_col)
    frame = frame.copy()

    weights: NDArray[np.float64] = np.ones(len(frame), dtype=float)
    drop_indices: set[int] = set()

    grouped = frame.reset_index().groupby([hex_col, brand_col], dropna=True)
    for (_, brand), group in grouped:
        if not brand or len(group) == 1:
            continue
        indices = group["index"].to_numpy(dtype=int)
        coords = group[[lat_col, lon_col]].to_numpy(dtype=float)
        distances = _pairwise_distance(coords)
        confidences = group.get(
            confidence_col,
            pd.Series(np.ones(len(group), dtype=float), index=group.index),
        ).astype(float)
        base_idx = np.argsort(-confidences.to_numpy(dtype=float))
        for order_position, idx_pos in enumerate(base_idx):
            idx = indices[idx_pos]
            if idx in drop_indices:
                continue
            close_mask = (distances[idx_pos] <= config.brand_distance_m) & (distances[idx_pos] > 0)
            neighbours = np.where(close_mask)[0]
            contribution = 0.0
            for neighbour in neighbours:
                neighbour_idx = indices[neighbour]
                if neighbour_idx == idx:
                    continue
                contribution += exp(-config.beta_per_km * (distances[idx_pos, neighbour] / 1000.0))
                if neighbour not in base_idx[: order_position + 1]:
                    drop_indices.add(neighbour_idx)
            weights[idx] = 1.0 / (1.0 + contribution)

    for _hex_value, group in frame.reset_index().groupby(hex_col):
        coords = group[[lat_col, lon_col]].to_numpy(dtype=float)
        distances = _pairwise_distance(coords)
        names = group[name_col].fillna("").astype(str).to_list()
        categories_series = group.get(
            category_col,
            pd.Series([None] * len(group), index=group.index),
        )
        categories = [
            value if isinstance(value, str) and value else None
            for value in categories_series.to_list()
        ]
        confidences = group.get(
            confidence_col,
            pd.Series(np.ones(len(group), dtype=float), index=group.index),
        ).to_numpy(dtype=float)
        indices = group["index"].to_numpy(dtype=int)
        for i in range(len(group)):
            if indices[i] in drop_indices:
                continue
            for j in range(i + 1, len(group)):
                if indices[j] in drop_indices:
                    continue
                category = categories[i] or categories[j]
                threshold = _resolve_threshold(config, category)
                if distances[i, j] > threshold:
                    continue
                similarity = fuzz.token_sort_ratio(names[i], names[j]) / 100.0
                if similarity < config.name_similarity:
                    continue
                if confidences[i] >= confidences[j]:
                    drop_indices.add(indices[j])
                else:
                    drop_indices.add(indices[i])

    deduped = frame.drop(index=list(drop_indices))
    deduped = deduped.assign(dedupe_weight=[weights[idx] for idx in deduped.index])
    return deduped


def _resolve_threshold(config: DedupeConfig, category: str | None) -> float:
    if config.distance_overrides and category and category in config.distance_overrides:
        return config.distance_overrides[category]
    return config.name_distance_m


def _pairwise_distance(coords: NDArray[np.float64]) -> NDArray[np.float64]:
    if coords.size == 0:
        return np.zeros((0, 0), dtype=float)
    lat = np.radians(coords[:, 0])
    lon = np.radians(coords[:, 1])
    sin_lat = np.sin((lat[:, None] - lat[None, :]) / 2.0)
    sin_lon = np.sin((lon[:, None] - lon[None, :]) / 2.0)
    a = sin_lat**2 + np.cos(lat)[:, None] * np.cos(lat)[None, :] * sin_lon**2
    distances = 2 * EARTH_RADIUS_M * np.arcsin(np.clip(np.sqrt(a), 0, 1))
    return np.asarray(distances, dtype=float)


__all__ = ["DedupeConfig", "deduplicate_pois", "ensure_hex_index"]
