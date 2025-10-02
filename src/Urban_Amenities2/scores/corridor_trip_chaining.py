from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(slots=True)
class CorridorConfig:
    max_detour_minutes: float = 10.0
    detour_decay: float = 5.0
    quality_column: str = "quality"
    detour_column: str = "detour_minutes"
    weight_column: str = "likelihood"
    hex_column: str = "hex_id"
    output_column: str = "CTE"

    def __post_init__(self) -> None:
        if self.max_detour_minutes <= 0:
            raise ValueError("max_detour_minutes must be positive")
        if self.detour_decay <= 0:
            raise ValueError("detour_decay must be positive")


class CorridorTripChaining:
    def __init__(self, config: CorridorConfig | None = None):
        self.config = config or CorridorConfig()

    def compute(self, chains: pd.DataFrame) -> pd.DataFrame:
        cfg = self.config
        for column in (cfg.quality_column, cfg.detour_column, cfg.weight_column, cfg.hex_column):
            if column not in chains.columns:
                raise KeyError(f"chains dataframe missing column {column}")
        unique_hexes = chains[cfg.hex_column].unique()
        filtered = chains[chains[cfg.detour_column] <= cfg.max_detour_minutes].copy()
        if filtered.empty:
            zeros = np.zeros(len(unique_hexes), dtype=float)
            return pd.DataFrame({cfg.hex_column: unique_hexes, cfg.output_column: zeros})
        filtered["weight"] = filtered[cfg.weight_column].fillna(1.0)
        filtered["adjusted_quality"] = filtered[cfg.quality_column] * np.exp(
            -filtered[cfg.detour_column] / cfg.detour_decay
        )
        filtered["score_component"] = filtered["adjusted_quality"] * filtered["weight"]
        aggregated = filtered.groupby(cfg.hex_column)["score_component"].sum().reset_index()
        missing_hexes = sorted(set(unique_hexes) - set(aggregated[cfg.hex_column]))
        if missing_hexes:
            zeros = pd.DataFrame({cfg.hex_column: missing_hexes, "score_component": 0.0})
            aggregated = pd.concat([aggregated, zeros], ignore_index=True)
        max_score = aggregated["score_component"].max()
        if max_score <= 0:
            aggregated[cfg.output_column] = 0.0
        else:
            aggregated[cfg.output_column] = aggregated["score_component"] / max_score * 100.0
        aggregated[cfg.output_column] = aggregated[cfg.output_column].clip(0.0, 100.0)
        return aggregated[[cfg.hex_column, cfg.output_column]]


__all__ = ["CorridorConfig", "CorridorTripChaining"]
