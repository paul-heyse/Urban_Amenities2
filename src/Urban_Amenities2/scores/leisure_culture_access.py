from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ..config.params import AUCSParams
from ..logging_utils import get_logger
from ..math.satiation import apply_satiation

LOGGER = get_logger("aucs.scores.lca")

LCA_CATEGORIES: tuple[str, ...] = (
    "restaurants",
    "cafes",
    "bars",
    "cinemas",
    "performing_arts",
    "museums_galleries",
    "parks_trails",
    "sports_rec",
)


@dataclass(slots=True)
class NoveltyConfig:
    max_bonus: float = 0.2
    reference_volatility: float = 1.0
    min_mean_views: float = 25.0
    views_column: str = "daily_views"
    volatility_column: str = "volatility"
    multiplier_column: str = "novelty_multiplier"

    def multiplier(self, volatility: float, mean_views: float | None = None) -> float:
        if mean_views is not None and mean_views < self.min_mean_views:
            return 1.0
        if volatility <= 0:
            return 1.0
        scale = min(volatility / self.reference_volatility, 1.0)
        return float(1.0 + scale * self.max_bonus)


@dataclass(slots=True)
class LeisureCultureAccessConfig:
    categories: tuple[str, ...] = LCA_CATEGORIES
    category_rho: Mapping[str, float] = field(default_factory=dict)
    category_kappa: Mapping[str, float] = field(default_factory=dict)
    category_column: str = "category"
    quality_column: str = "quality"
    weight_column: str = "weight"
    output_column: str = "LCA"
    cross_rho: float = 0.6
    cross_weights: Mapping[str, float] = field(default_factory=dict)
    category_groups: Mapping[str, str] = field(default_factory=dict)
    novelty: NoveltyConfig = field(default_factory=NoveltyConfig)
    exposure_scale: float = 6.0

    @classmethod
    def from_params(cls, params: AUCSParams) -> LeisureCultureAccessConfig:
        categories = tuple(params.categories.leisure or LCA_CATEGORIES)
        rho_map = params.derived_ces_rho(categories)
        satiation = params.derived_satiation()
        cross = params.leisure_cross_category
        novelty_cfg = NoveltyConfig(
            max_bonus=cross.novelty.max_bonus,
            reference_volatility=cross.novelty.reference_volatility,
            min_mean_views=cross.novelty.min_mean_views,
        )
        groups = cross.category_groups or {category: category for category in categories}
        weights = cross.weights or {category: 1.0 for category in categories}
        kappa_map: dict[str, float] = {}
        for category in categories:
            if category in satiation:
                kappa_map[category] = float(satiation[category])
            elif "leisure" in satiation:
                kappa_map[category] = float(satiation["leisure"])
            else:
                kappa_map[category] = 0.3
        return cls(
            categories=categories,
            category_rho=rho_map,
            category_kappa=kappa_map,
            cross_rho=float(cross.elasticity_zeta),
            cross_weights=weights,
            category_groups=groups,
            novelty=novelty_cfg,
        )

    def rho_for(self, category: str) -> float:
        return float(self.category_rho.get(category, 0.6))

    def kappa_for(self, category: str) -> float:
        return float(self.category_kappa.get(category, 0.3))

    def group_for(self, category: str) -> str:
        return self.category_groups.get(category, category)

    def weight_for(self, category: str) -> float:
        key = self.group_for(category)
        return float(self.cross_weights.get(key, self.cross_weights.get(category, 1.0)))


def compute_pageview_volatility(values: Sequence[float]) -> tuple[float, float]:
    array = np.asarray(list(values), dtype=float)
    array = array[np.isfinite(array)]
    if array.size == 0:
        return 0.0, 0.0
    mean = float(array.mean())
    if mean <= 0:
        return 0.0, mean
    stdev = float(array.std(ddof=0))
    return float(stdev / mean), mean


def compute_novelty_table(frame: pd.DataFrame, config: NoveltyConfig) -> pd.DataFrame:
    if "poi_id" not in frame.columns:
        raise KeyError("novelty table requires 'poi_id' column")
    if config.volatility_column in frame.columns:
        volatility = frame[config.volatility_column].astype(float)
        mean_views = frame.get("mean_views")
    elif config.views_column in frame.columns:
        volatility_values: list[float] = []
        mean_values: list[float] = []
        for values in frame[config.views_column]:
            if isinstance(values, Sequence) and not isinstance(values, (str, bytes)):
                vol, mean = compute_pageview_volatility(values)
            else:
                vol, mean = (0.0, 0.0)
            volatility_values.append(vol)
            mean_values.append(mean)
        volatility = pd.Series(volatility_values, index=frame.index)
        mean_views = pd.Series(mean_values, index=frame.index)
    else:
        raise KeyError(
            f"novelty table requires either '{config.volatility_column}' or '{config.views_column}' column"
        )
    mean_views = mean_views.astype(float) if mean_views is not None else None
    multipliers = []
    for idx, vol in volatility.items():
        mean_value = float(mean_views.loc[idx]) if mean_views is not None else None
        multipliers.append(config.multiplier(float(vol), mean_value))
    table = frame[["poi_id"]].copy()
    table[config.volatility_column] = volatility.to_numpy()
    if mean_views is not None:
        table["mean_views"] = mean_views.to_numpy()
    table[config.multiplier_column] = multipliers
    return table


class LeisureCultureAccessCalculator:
    def __init__(
        self,
        config: LeisureCultureAccessConfig | None = None,
    ) -> None:
        self.config = config or LeisureCultureAccessConfig()

    @classmethod
    def from_params(cls, params: AUCSParams) -> LeisureCultureAccessCalculator:
        return cls(LeisureCultureAccessConfig.from_params(params))

    def _prepare_pois(
        self,
        pois: pd.DataFrame,
        novelty: pd.DataFrame | None,
    ) -> pd.DataFrame:
        if "poi_id" not in pois.columns:
            raise KeyError("pois dataframe requires 'poi_id' column")
        if self.config.category_column not in pois.columns:
            raise KeyError(f"pois dataframe missing '{self.config.category_column}' column")
        if self.config.quality_column not in pois.columns:
            raise KeyError(f"pois dataframe missing '{self.config.quality_column}' column")
        frame = pois.copy()
        frame[self.config.category_column] = (
            frame[self.config.category_column].astype(str).str.lower()
        )
        frame = frame[frame[self.config.category_column].isin(self.config.categories)]
        multiplier_col = self.config.novelty.multiplier_column
        if novelty is not None:
            novelty_table = compute_novelty_table(novelty, self.config.novelty)[
                ["poi_id", multiplier_col]
            ]
            frame = frame.merge(novelty_table, on="poi_id", how="left")
        else:
            frame[multiplier_col] = 1.0
        frame[multiplier_col] = frame[multiplier_col].fillna(1.0)
        frame["quality_adjusted"] = (
            frame[self.config.quality_column].astype(float).clip(lower=0.0) * frame[multiplier_col]
        )
        return frame

    def _category_scores(
        self,
        pois: pd.DataFrame,
        accessibility: pd.DataFrame,
        *,
        id_column: str,
    ) -> pd.DataFrame:
        if id_column not in accessibility.columns:
            raise KeyError(f"accessibility dataframe missing '{id_column}' column")
        if "poi_id" not in accessibility.columns:
            raise KeyError("accessibility dataframe requires 'poi_id' column")
        if self.config.weight_column not in accessibility.columns:
            raise KeyError(f"accessibility dataframe missing '{self.config.weight_column}' column")
        merged = accessibility.merge(pois, on="poi_id", how="inner")
        if merged.empty:
            return pd.DataFrame({id_column: [], "category": [], "score": []})
        merged[self.config.weight_column] = merged[self.config.weight_column].clip(lower=0.0)
        scores: list[dict[str, float | str]] = []
        for category, group in merged.groupby(self.config.category_column):
            rho = self.config.rho_for(category)

            def _aggregate(df: pd.DataFrame, rho_value: float = rho) -> float:
                weights = df[self.config.weight_column].to_numpy(dtype=float).clip(0.0)
                if weights.sum() == 0:
                    return 0.0
                weights = weights / weights.sum()
                quality = df["quality_adjusted"].to_numpy(dtype=float).clip(0.0, 100.0) / 100.0
                if np.all(quality == 0):
                    return 0.0
                if abs(rho_value) < 1e-6:
                    return float(np.exp(np.sum(weights * np.log(np.clip(quality, 1e-12, 1.0)))))
                if abs(rho_value - 1.0) < 1e-6:
                    return float(np.sum(weights * quality))
                return float(
                    np.power(np.sum(weights * np.power(quality, rho_value)), 1.0 / rho_value)
                )

            intensity = group.groupby(id_column, dropna=False).apply(
                _aggregate, include_groups=False
            )
            if intensity.empty:
                continue
            exposure = np.maximum(intensity.to_numpy(dtype=float) * self.config.exposure_scale, 0.0)
            kappa = self.config.kappa_for(category)
            saturated = apply_satiation(exposure, kappa)
            for hex_id, value in zip(intensity.index, saturated, strict=False):
                scores.append(
                    {
                        id_column: hex_id,
                        "category": category,
                        "score": float(np.clip(value, 0.0, 100.0)),
                    }
                )
        if not scores:
            return pd.DataFrame({id_column: [], "category": [], "score": []})
        return pd.DataFrame(scores)

    def _aggregate_cross_category(self, row: pd.Series) -> float:
        values: list[float] = []
        weights: list[float] = []
        for category in self.config.categories:
            score = float(row.get(category, 0.0))
            values.append(np.clip(score / 100.0, 0.0, 1.0))
            weights.append(max(self.config.weight_for(category), 0.0))
        if not values or all(weight == 0 for weight in weights):
            return 0.0
        weight_array = np.asarray(weights, dtype=float)
        if weight_array.sum() == 0:
            return 0.0
        weight_array = weight_array / weight_array.sum()
        value_array = np.asarray(values, dtype=float)
        rho = self.config.cross_rho
        if np.all(value_array == 0):
            return 0.0
        if abs(rho) < 1e-6:
            aggregated = float(
                np.exp(np.sum(weight_array * np.log(np.clip(value_array, 1e-12, 1.0))))
            )
        elif abs(rho - 1.0) < 1e-6:
            aggregated = float(np.sum(weight_array * value_array))
        else:
            aggregated = float(
                np.power(np.sum(weight_array * np.power(value_array, rho)), 1.0 / rho)
            )
        return float(np.clip(aggregated * 100.0, 0.0, 100.0))

    def compute(
        self,
        pois: pd.DataFrame,
        accessibility: pd.DataFrame,
        novelty: pd.DataFrame | None = None,
        *,
        id_column: str = "hex_id",
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        prepared = self._prepare_pois(pois, novelty)
        category_scores = self._category_scores(prepared, accessibility, id_column=id_column)
        if category_scores.empty:
            empty = pd.DataFrame(
                {id_column: [], self.config.output_column: [], "category_scores": []}
            )
            return empty, category_scores
        matrix = (
            category_scores.pivot(index=id_column, columns="category", values="score")
            .reindex(columns=self.config.categories, fill_value=0.0)
            .fillna(0.0)
        )
        summary = matrix.copy()
        summary[self.config.output_column] = summary.apply(self._aggregate_cross_category, axis=1)
        summary["category_scores"] = summary.apply(
            lambda row: {category: float(row[category]) for category in self.config.categories},
            axis=1,
        )
        summary = summary[[self.config.output_column, "category_scores"]]
        summary.index.name = id_column
        summary = summary.reset_index()
        category_scores = category_scores.sort_values([id_column, "category"]).reset_index(
            drop=True
        )
        LOGGER.info(
            "lca_compute",
            hexes=len(summary),
            categories=len(self.config.categories),
        )
        return summary[[id_column, self.config.output_column, "category_scores"]], category_scores


__all__ = [
    "LCA_CATEGORIES",
    "NoveltyConfig",
    "LeisureCultureAccessConfig",
    "LeisureCultureAccessCalculator",
    "compute_novelty_table",
    "compute_pageview_volatility",
]
