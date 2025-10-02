from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence

import numpy as np
import pandas as pd

from ..logging_utils import get_logger
from ..math.ces import compute_z
from ..math.diversity import DiversityConfig, compute_diversity
from ..math.satiation import apply_satiation
from .penalties import shortfall_penalty

LOGGER = get_logger("aucs.scores.ea")


@dataclass
class EssentialCategoryConfig:
    rho: float
    kappa: float
    diversity: DiversityConfig


@dataclass
class EssentialsAccessConfig:
    categories: Sequence[str]
    category_params: Dict[str, EssentialCategoryConfig]
    shortfall_threshold: float = 20.0
    shortfall_penalty: float = 2.0
    shortfall_cap: float = 8.0
    top_k: int = 5
    batch_size: int = 512


class EssentialsAccessCalculator:
    def __init__(self, config: EssentialsAccessConfig):
        self.config = config

    def _prepare(self, pois: pd.DataFrame, accessibility: pd.DataFrame) -> pd.DataFrame:
        frame = accessibility.merge(
            pois[["poi_id", "aucstype", "quality", "brand", "name"]],
            on="poi_id",
            how="left",
        )
        if "hex_id" not in frame.columns and "origin_hex" in frame.columns:
            frame = frame.rename(columns={"origin_hex": "hex_id"})
        frame["category"] = frame["aucstype"]
        frame["subtype"] = frame["brand"].fillna(frame["category"])
        frame["qw"] = frame["quality"] * frame["weight"]
        return frame

    def compute(
        self,
        pois: pd.DataFrame,
        accessibility: pd.DataFrame,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        data = self._prepare(pois, accessibility)
        hex_ids = data["hex_id"].unique()
        diversity_config = {}
        for category in self.config.categories:
            params = self.config.category_params.get(category, EssentialCategoryConfig(1.0, 1.0, DiversityConfig()))
            diversity_config[category] = params.diversity
        diversity = compute_diversity(
            data,
            value_column="qw",
            group_columns=["hex_id", "category"],
            subtype_column="subtype",
            config=diversity_config,
        )
        category_frames: List[pd.DataFrame] = []
        explainability: Dict[str, Dict[str, List[dict[str, object]]]] = {hex_id: {} for hex_id in hex_ids}
        batches = [hex_ids] if self.config.batch_size <= 0 else [hex_ids[i : i + self.config.batch_size] for i in range(0, len(hex_ids), self.config.batch_size)]
        for batch_index, batch_hexes in enumerate(batches, start=1):
            LOGGER.info("ea_batch", batch=batch_index, total=len(batches), size=len(batch_hexes))
            batch_data = data[data["hex_id"].isin(batch_hexes)]
            for category in self.config.categories:
                params = self.config.category_params.get(category, EssentialCategoryConfig(1.0, 1.0, DiversityConfig()))
                cat_data = batch_data[batch_data["category"] == category]
                if cat_data.empty:
                    empty = pd.DataFrame({"hex_id": batch_hexes, "category": category, "satiation": 0.0, "diversity_bonus": 0.0, "entropy": 0.0, "score": 0.0})
                    category_frames.append(empty)
                    for hex_id in batch_hexes:
                        explainability.setdefault(hex_id, {})[category] = []
                    continue
                rho = params.rho
                z_values = compute_z(cat_data["quality"].to_numpy(), cat_data["weight"].to_numpy(), rho)
                cat_data = cat_data.assign(z=z_values)
                aggregated = cat_data.groupby("hex_id")["z"].sum()
                V = aggregated.pow(1.0 / rho)
                satiation_scores = apply_satiation(V.to_numpy(), params.kappa)
                frame = pd.DataFrame({"hex_id": aggregated.index, "category": category, "V": V, "satiation": satiation_scores})
                frame = frame.merge(diversity[diversity["category"] == category], on=["hex_id", "category"], how="left")
                frame["diversity_bonus"] = frame["diversity_bonus"].fillna(0.0)
                frame["entropy"] = frame["entropy"].fillna(0.0)
                frame["score"] = np.clip(frame["satiation"] + frame["diversity_bonus"], 0, 100)
                category_frames.append(frame)
                for hex_id in frame["hex_id"]:
                    explainability.setdefault(hex_id, {})[category] = self._extract_top(cat_data, hex_id, category)
        category_scores = pd.concat(category_frames, ignore_index=True) if category_frames else pd.DataFrame()
        ea_records = []
        for hex_id, group in category_scores.groupby("hex_id"):
            penalty = shortfall_penalty(group["score"], threshold=self.config.shortfall_threshold, per_miss=self.config.shortfall_penalty, cap=self.config.shortfall_cap)
            mean_score = group["score"].mean() if not group.empty else 0.0
            final_score = max(mean_score - penalty, 0.0)
            ea_records.append(
                {
                    "hex_id": hex_id,
                    "EA": final_score,
                    "penalty": penalty,
                    "category_scores": group.set_index("category")["score"].to_dict(),
                    "contributors": explainability.get(hex_id, {}),
                }
            )
        ea_scores = pd.DataFrame.from_records(ea_records)
        return ea_scores, category_scores

    def _extract_top(self, cat_data: pd.DataFrame, hex_id: str, category: str) -> List[dict[str, object]]:
        subset = cat_data[cat_data["hex_id"] == hex_id]
        if subset.empty:
            return []
        ranked = subset.sort_values("z", ascending=False).head(self.config.top_k)
        return [
            {
                "poi_id": record["poi_id"],
                "name": record.get("name"),
                "aucstype": category,
                "brand": record.get("brand"),
                "contribution": record["z"],
            }
            for record in ranked[["poi_id", "name", "brand", "z"]].to_dict("records")
        ]


__all__ = ["EssentialsAccessCalculator", "EssentialsAccessConfig", "EssentialCategoryConfig"]
