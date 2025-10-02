from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Sequence

import numpy as np
import pandas as pd

from ..math.logsum import (
    ModeUtilityParams,
    mode_utility,
    nest_inclusive,
    time_weighted_accessibility,
    top_level_logsum,
)


@dataclass
class NestConfig:
    modes: Sequence[str]
    mu: float


@dataclass
class AccessibilityConfig:
    mode_params: Dict[str, ModeUtilityParams]
    nests: Dict[str, NestConfig]
    mu_top: float
    time_weights: Sequence[float]


class AccessibilityMatrixBuilder:
    def __init__(self, config: AccessibilityConfig):
        self.config = config

    def build(self, frame: pd.DataFrame) -> pd.DataFrame:
        origins = frame["origin_hex"].unique()
        pois = frame["poi_id"].unique()
        modes = list(self.config.mode_params.keys())
        periods = list(sorted(frame["period"].dropna().unique())) or [None]
        gtc_array = np.full((len(origins), len(pois), len(modes), len(periods)), np.inf)
        comfort_array = np.zeros_like(gtc_array)
        origin_index = {hex_id: idx for idx, hex_id in enumerate(origins)}
        poi_index = {poi: idx for idx, poi in enumerate(pois)}
        mode_index = {mode: idx for idx, mode in enumerate(modes)}
        period_index = {period: idx for idx, period in enumerate(periods)}
        for row in frame.itertuples():
            i = origin_index[row.origin_hex]
            j = poi_index[row.poi_id]
            k = mode_index[row.mode]
            t = period_index.get(row.period, 0)
            gtc_array[i, j, k, t] = row.gtc
            comfort_array[i, j, k, t] = getattr(row, "comfort", 0.0)
        utilities = np.zeros_like(gtc_array)
        for mode, params in self.config.mode_params.items():
            k = mode_index[mode]
            utilities[:, :, k, :] = mode_utility(gtc_array[:, :, k, :], comfort_array[:, :, k, :], params)
        nest_values = []
        for nest in self.config.nests.values():
            indices = [mode_index[mode] for mode in nest.modes if mode in mode_index]
            if not indices:
                continue
            subset = utilities[:, :, indices, :]
            nest_util = nest_inclusive(subset, nest.mu)
            nest_values.append(nest_util[..., np.newaxis])
        if not nest_values:
            raise ValueError("No nests configured with valid modes")
        stacked = np.concatenate(nest_values, axis=-1)
        inclusive_value = top_level_logsum(stacked, self.config.mu_top)
        flattened = utilities.reshape(len(origins), len(pois), -1)
        if flattened.shape[-1] != len(self.config.time_weights):
            raise ValueError("time_weights must match modes × periods")
        weights = time_weighted_accessibility(flattened, self.config.time_weights)
        result = pd.DataFrame(
            {
                "origin_hex": np.repeat(origins, len(pois)),
                "poi_id": np.tile(pois, len(origins)),
                "weight": weights.reshape(len(origins), len(pois)).ravel(),
                "inclusive_value": inclusive_value.reshape(len(origins), len(pois)).ravel(),
            }
        )
        result["weight"] = result["weight"].fillna(0.0)
        result.loc[~np.isfinite(result["weight"]), "weight"] = 0.0
        return result


__all__ = ["AccessibilityMatrixBuilder", "AccessibilityConfig", "NestConfig"]
