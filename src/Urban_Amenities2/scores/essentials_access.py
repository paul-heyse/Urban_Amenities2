from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..config.params import AUCSParams, CategoryDiversityConfig
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

    def __post_init__(self) -> None:
        if not np.isfinite(self.rho):
            raise ValueError("rho must be finite")
        if self.rho > 1.0:
            raise ValueError("rho must be less than or equal to 1")
        if self.kappa <= 0:
            raise ValueError("kappa must be positive")


@dataclass
class EssentialsAccessConfig:
    categories: Sequence[str]
    category_params: dict[str, EssentialCategoryConfig]
    shortfall_threshold: float = 20.0
    shortfall_penalty: float = 2.0
    shortfall_cap: float = 8.0
    top_k: int = 5
    batch_size: int = 512

    @classmethod
    def from_params(
        cls,
        params: AUCSParams,
        categories: Sequence[str] | None = None,
        shortfall_threshold: float | None = None,
        shortfall_penalty: float | None = None,
        shortfall_cap: float | None = None,
        top_k: int | None = None,
        batch_size: int | None = None,
    ) -> EssentialsAccessConfig:
        category_cfg = params.categories
        category_list = list(categories or category_cfg.essentials)
        if not category_list:
            raise ValueError("At least one category is required for essentials access")

        rho_map = category_cfg.derived_rho(category_list)
        kappa_map = params.derived_satiation()

        def _diversity_for(category: str) -> DiversityConfig:
            config = category_cfg.get_diversity(category)
            if isinstance(config, CategoryDiversityConfig):
                return DiversityConfig(
                    weight=config.weight,
                    min_multiplier=config.min_multiplier,
                    max_multiplier=config.max_multiplier,
                )
            return DiversityConfig()

        category_params: dict[str, EssentialCategoryConfig] = {}
        for name in category_list:
            rho = rho_map.get(name)
            if rho is None:
                raise ValueError(f"Missing CES rho for category {name}")
            kappa = kappa_map.get(name)
            if kappa is None:
                raise ValueError(f"Missing satiation kappa for category {name}")
            category_params[name] = EssentialCategoryConfig(
                rho=rho,
                kappa=kappa,
                diversity=_diversity_for(name),
            )

        kwargs: dict[str, float | int] = {}
        if shortfall_threshold is not None:
            kwargs["shortfall_threshold"] = shortfall_threshold
        if shortfall_penalty is not None:
            kwargs["shortfall_penalty"] = shortfall_penalty
        if shortfall_cap is not None:
            kwargs["shortfall_cap"] = shortfall_cap
        if top_k is not None:
            kwargs["top_k"] = top_k
        if batch_size is not None:
            kwargs["batch_size"] = batch_size

        return cls(categories=category_list, category_params=category_params, **kwargs)


class EssentialsAccessCalculator:
    def __init__(self, config: EssentialsAccessConfig):
        self.config = config

    def _prepare(self, pois: pd.DataFrame, accessibility: pd.DataFrame) -> pd.DataFrame:
        base_columns = ["poi_id", "aucstype", "quality", "brand", "name"]
        optional_columns = [col for col in ("quality_components", "brand_penalty", "brand_weight") if col in pois.columns]
        frame = accessibility.merge(
            pois[base_columns + optional_columns],
            on="poi_id",
            how="left",
        )
        if "hex_id" not in frame.columns and "origin_hex" in frame.columns:
            frame = frame.rename(columns={"origin_hex": "hex_id"})
        frame["category"] = frame["aucstype"]
        frame["subtype"] = frame["brand"].fillna(frame["category"])
        frame["quality_original"] = frame["quality"]
        if "brand_penalty" in frame.columns:
            frame["quality"] = frame["quality"] * frame["brand_penalty"].fillna(1.0)
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
        category_frames: list[pd.DataFrame] = []
        explainability: dict[str, dict[str, list[dict[str, object]]]] = {hex_id: {} for hex_id in hex_ids}
        batches = [hex_ids] if self.config.batch_size <= 0 else [hex_ids[i : i + self.config.batch_size] for i in range(0, len(hex_ids), self.config.batch_size)]
        for batch_index, batch_hexes in enumerate(batches, start=1):
            LOGGER.info("ea_batch", batch=batch_index, total=len(batches), size=len(batch_hexes))
            batch_data = data[data["hex_id"].isin(batch_hexes)]
            for category in self.config.categories:
                params = self.config.category_params.get(category, EssentialCategoryConfig(1.0, 1.0, DiversityConfig()))
                cat_data = batch_data[batch_data["category"] == category]
                if cat_data.empty:
                    empty = pd.DataFrame(
                        {
                            "hex_id": batch_hexes,
                            "category": category,
                            "satiation": 0.0,
                            "diversity_multiplier": 1.0,
                            "entropy": 0.0,
                            "score": 0.0,
                        }
                    )
                    category_frames.append(empty)
                    for hex_id in batch_hexes:
                        explainability.setdefault(hex_id, {})[category] = []
                    continue
                rho = params.rho
                z_values = compute_z(cat_data["quality"].to_numpy(), cat_data["weight"].to_numpy(), rho)
                cat_data = cat_data.assign(z=z_values)
                aggregated = cat_data.groupby("hex_id", as_index=False)["z"].sum()
                V = aggregated["z"].pow(1.0 / rho)
                satiation_scores = apply_satiation(V.to_numpy(), params.kappa)
                frame = pd.DataFrame(
                    {
                        "hex_id": aggregated["hex_id"],
                        "category": category,
                        "V": V,
                        "satiation": satiation_scores,
                    }
                )
                frame = frame.merge(diversity[diversity["category"] == category], on=["hex_id", "category"], how="left")
                frame["diversity_multiplier"] = frame["diversity_multiplier"].fillna(1.0)
                frame["entropy"] = frame["entropy"].fillna(0.0)
                frame["score"] = np.clip(frame["satiation"] * frame["diversity_multiplier"], 0, 100)
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

    def _extract_top(self, cat_data: pd.DataFrame, hex_id: str, category: str) -> list[dict[str, object]]:
        subset = cat_data[cat_data["hex_id"] == hex_id]
        if subset.empty:
            return []
        ranked = subset.sort_values("z", ascending=False).head(self.config.top_k)
        columns = [
            column
            for column in [
                "poi_id",
                "name",
                "brand",
                "z",
                "quality",
                "quality_components",
                "brand_penalty",
            ]
            if column in ranked.columns
        ]
        return [
            {
                "poi_id": record.get("poi_id"),
                "name": record.get("name"),
                "aucstype": category,
                "brand": record.get("brand"),
                "contribution": record.get("z"),
                "quality": record.get("quality"),
                "quality_components": record.get("quality_components"),
                "brand_penalty": record.get("brand_penalty"),
            }
            for record in ranked[columns].to_dict("records")
        ]


__all__ = ["EssentialsAccessCalculator", "EssentialsAccessConfig", "EssentialCategoryConfig"]
