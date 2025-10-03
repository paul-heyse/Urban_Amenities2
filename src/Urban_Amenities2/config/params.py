"""Pydantic models describing AUCS 2.0 configuration."""

from __future__ import annotations

from collections.abc import Iterable
from functools import cached_property
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class _BaseConfig(BaseModel):
    """Base model that forbids unknown fields and allows reassignment validation."""

    model_config = {
        "extra": "forbid",
        "validate_assignment": True,
    }


class GridConfig(_BaseConfig):
    """Configuration for the spatial grid resolution and search limits."""

    hex_size_m: float = Field(
        ..., gt=0, description="Approximate edge length of the grid in metres"
    )
    isochrone_minutes: list[int] = Field(
        ..., min_length=1, description="Minute values for isochrone rings"
    )
    search_cap_minutes: int = Field(
        ..., gt=0, description="Maximum travel minutes to consider during searches"
    )

    @model_validator(mode="after")
    def _validate_isochrones(self) -> GridConfig:
        if sorted(self.isochrone_minutes) != self.isochrone_minutes:
            msg = "isochrone_minutes must be sorted ascending"
            raise ValueError(msg)
        return self


class SubscoreWeights(_BaseConfig):
    """Weights for each subscore. They must sum to 100."""

    EA: float
    LCA: float
    MUHAA: float
    JEA: float
    MORR: float
    CTE: float
    SOU: float

    @model_validator(mode="after")
    def _check_total(cls, values: SubscoreWeights) -> SubscoreWeights:
        total = sum(
            getattr(values, field) for field in ("EA", "LCA", "MUHAA", "JEA", "MORR", "CTE", "SOU")
        )
        if round(total, 2) != 100.0:
            msg = f"Subscore weights must total 100, received {total:.2f}"
            raise ValueError(msg)
        return values


class TimeSliceConfig(_BaseConfig):
    """Configuration for a time-of-day slice used in model computation."""

    id: str
    weight: float = Field(..., gt=0)
    vot_per_hour: float = Field(..., gt=0, alias="VOT_per_hour")


class ModeConfig(_BaseConfig):
    """Parameters controlling a transport mode in the nested logit."""

    name: str
    theta_iv: float
    theta_wait: float
    theta_walk: float
    transfer_penalty_min: float = Field(..., ge=0)
    half_life_min: float = Field(..., gt=0)
    beta0: float
    reliability_buffer: float = Field(0.0, ge=0)
    max_access_distance_m: float | None = Field(None, gt=0)
    enabled: bool = True

    @cached_property
    def decay_alpha(self) -> float:
        """Continuous-time decay coefficient derived from the half-life."""

        from math import log

        return log(2.0) / self.half_life_min


class NestConfig(_BaseConfig):
    """Grouping of modes for the nested logit."""

    id: str
    modes: list[str] = Field(..., min_length=1)
    mu: float = Field(..., gt=0)
    eta: float = Field(..., gt=0)


class LogitConfig(_BaseConfig):
    """Configuration for the top-level logit."""

    mu_top: float = Field(..., gt=0)


class CarryPenaltyConfig(_BaseConfig):
    """Penalties applied when users have to carry goods."""

    category_multipliers: dict[str, float]
    per_mode_extra_minutes: dict[str, float]


class QualityConfig(_BaseConfig):
    """Quality scoring parameters."""

    component_weights: dict[str, float]
    z_clip_abs: float = Field(..., ge=0)
    opening_hours_bonus_xi: float = Field(..., ge=0)
    dedupe_beta_per_km: float = Field(..., ge=0)
    hours_defaults: dict[str, str] = Field(default_factory=dict)


class CategoryDiversityConfig(_BaseConfig):
    """Diversity configuration for leisure and essentials."""

    weight: float = Field(0.2, ge=0)
    min_multiplier: float = Field(1.0, gt=0)
    max_multiplier: float = Field(1.2, gt=0)

    @model_validator(mode="after")
    def _check_range(self) -> CategoryDiversityConfig:
        if self.max_multiplier < self.min_multiplier:
            msg = "max_multiplier must be >= min_multiplier"
            raise ValueError(msg)
        return self


class CategoryConfig(_BaseConfig):
    """Category level configuration."""

    essentials: list[str]
    leisure: list[str]
    ces_rho: dict[str, float] | float
    satiation_mode: Literal["none", "anchor", "direct"] = "none"
    satiation_kappa: dict[str, float] | float | None = None
    satiation_targets: dict[str, dict[str, float]] | None = None
    diversity: dict[str, CategoryDiversityConfig] = Field(default_factory=dict)

    def derived_satiation(self) -> dict[str, float]:
        """Compute satiation kappa per category based on the selected mode."""

        from math import log

        if self.satiation_mode == "direct":
            if isinstance(self.satiation_kappa, dict):
                output: dict[str, float] = {}
                for category, value in self.satiation_kappa.items():
                    if value <= 0:
                        msg = f"Satiation kappa for {category} must be positive"
                        raise ValueError(msg)
                    output[category] = float(value)
                return output
            if isinstance(self.satiation_kappa, (int, float)):
                if self.satiation_kappa <= 0:
                    raise ValueError("Satiation kappa must be positive")
                return {
                    name: float(self.satiation_kappa) for name in self.essentials + self.leisure
                }
            msg = "Direct satiation requires satiation_kappa values"
            raise ValueError(msg)
        if self.satiation_mode == "anchor":
            if not self.satiation_targets:
                msg = "Anchor satiation requires satiation_targets"
                raise ValueError(msg)
            output: dict[str, float] = {}
            for category, target in self.satiation_targets.items():
                score = target.get("score")
                value = target.get("value")
                if score is None or value is None:
                    msg = f"Missing score/value for satiation target {category}"
                    raise ValueError(msg)
                output[category] = -log(1 - score / 100.0) / value
            return output
        return {}

    def derived_rho(self, categories: Iterable[str] | None = None) -> dict[str, float]:
        names = list(categories or (self.essentials + self.leisure))
        if isinstance(self.ces_rho, dict):
            mapping = {}
            for name in names:
                value = self.ces_rho.get(name)
                if value is None:
                    msg = f"Missing CES rho for category {name}"
                    raise ValueError(msg)
                mapping[name] = float(value)
        else:
            mapping = {name: float(self.ces_rho) for name in names}
        for name, value in mapping.items():
            if value >= 1:
                msg = f"CES rho for {name} must be less than 1"
                raise ValueError(msg)
        return mapping

    def get_diversity(self, category: str) -> CategoryDiversityConfig | None:
        if category in self.diversity:
            return self.diversity[category]
        if category in self.essentials and "essentials" in self.diversity:
            return self.diversity["essentials"]
        if category in self.leisure and "leisure" in self.diversity:
            return self.diversity["leisure"]
        return None


class NoveltyBonusConfig(_BaseConfig):
    """Configuration for the leisure novelty bonus."""

    max_bonus: float = Field(0.2, ge=0)
    reference_volatility: float = Field(1.0, gt=0)
    min_mean_views: float = Field(1.0, ge=0)


class LeisureCrossCategoryConfig(_BaseConfig):
    weights: dict[str, float]
    elasticity_zeta: float
    category_groups: dict[str, str] = Field(default_factory=dict)
    novelty: NoveltyBonusConfig = Field(default_factory=NoveltyBonusConfig)

    @model_validator(mode="after")
    def _validate_weights(self) -> LeisureCrossCategoryConfig:
        if not self.weights:
            raise ValueError("leisure cross-category weights must not be empty")
        negative = {key: value for key, value in self.weights.items() if value < 0}
        if negative:
            msg = f"weights must be non-negative, received negatives for {sorted(negative)}"
            raise ValueError(msg)
        return self


class HubsAirportsConfig(_BaseConfig):
    hub_mass_weights: dict[str, float]
    hub_decay_alpha: float = Field(..., gt=0)
    airport_decay_alpha: float = Field(..., gt=0)
    contributions: dict[str, float] = Field(default_factory=lambda: {"hub": 0.7, "airport": 0.3})
    airport_weights: dict[str, float] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_config(self) -> HubsAirportsConfig:
        if not self.hub_mass_weights:
            raise ValueError("hub_mass_weights must not be empty")
        if any(value < 0 for value in self.hub_mass_weights.values()):
            raise ValueError("hub mass weights must be non-negative")
        if all(value == 0 for value in self.hub_mass_weights.values()):
            raise ValueError("hub mass weights must contain positive values")
        total = sum(self.contributions.values())
        if total <= 0:
            raise ValueError("at least one MUHAA contribution must be positive")
        return self


class JobsEducationConfig(_BaseConfig):
    university_weight_kappa: float
    industry_weights: dict[str, float]


class MORRConfig(_BaseConfig):
    frequent_exposure: float
    span: float
    reliability: float
    redundancy: float
    micromobility: float


class HubDefinitionConfig(_BaseConfig):
    id: str
    name: str
    lat: float
    lon: float


class CorridorConfig(_BaseConfig):
    max_paths: int = Field(..., gt=0)
    stop_buffer_m: float = Field(..., ge=0)
    detour_cap_min: float = Field(..., ge=0)
    pair_categories: list[list[str]] = Field(default_factory=list)
    walk_decay_alpha: float = Field(..., ge=0)
    major_hubs: dict[str, list[HubDefinitionConfig]] = Field(default_factory=dict)
    chain_weights: dict[str, float] = Field(default_factory=dict)
    min_stop_count: int = Field(5, ge=0)
    cache_size: int = Field(1024, ge=0)

    @model_validator(mode="after")
    def _validate_pairs(self) -> CorridorConfig:
        for pair in self.pair_categories:
            if len(pair) != 2:
                msg = "pair_categories entries must have exactly two categories"
                raise ValueError(msg)
        return self


class SeasonalityConfig(_BaseConfig):
    comfort_index_default: float
    weather_adjustments: dict[str, float] = Field(default_factory=dict)


class NormalizationStandard(_BaseConfig):
    name: str
    percentile: float


class NormalizationConfig(_BaseConfig):
    mode: Literal["metro", "global"] = "metro"
    metro_percentile: float = Field(95.0, ge=0, le=100)
    standards: list[NormalizationStandard] = Field(default_factory=list)


class ComputeConfig(_BaseConfig):
    topK_per_category: int = Field(..., gt=0)
    hub_max_minutes: int = Field(..., gt=0)
    preload_hex_neighbors: bool = True
    cache_dir: str | None = None


class AUCSParams(_BaseConfig):
    """Root configuration object containing all parameters."""

    grid: GridConfig
    subscores: SubscoreWeights
    time_slices: list[TimeSliceConfig]
    modes: dict[str, ModeConfig]
    nests: list[NestConfig]
    logit: LogitConfig
    carry_penalty: CarryPenaltyConfig
    quality: QualityConfig
    categories: CategoryConfig
    leisure_cross_category: LeisureCrossCategoryConfig
    hubs_airports: HubsAirportsConfig
    jobs_education: JobsEducationConfig
    morr: MORRConfig
    corridor: CorridorConfig
    seasonality: SeasonalityConfig
    normalization: NormalizationConfig
    compute: ComputeConfig

    @model_validator(mode="after")
    def _validate_relationships(self) -> AUCSParams:
        defined_modes = set(self.modes.keys())
        for nest in self.nests:
            missing = set(nest.modes) - defined_modes
            if missing:
                msg = f"Nest {nest.id} references undefined modes: {sorted(missing)}"
                raise ValueError(msg)
        return self

    def derived_mode_alphas(self) -> dict[str, float]:
        """Return the decay coefficient per mode."""

        return {mode_name: mode.decay_alpha for mode_name, mode in self.modes.items()}

    def derived_satiation(self) -> dict[str, float]:
        """Expose derived satiation kappas from the category configuration."""

        return self.categories.derived_satiation()

    def derived_ces_rho(self, categories: Iterable[str] | None = None) -> dict[str, float]:
        """Expose CES rho values per category."""

        return self.categories.derived_rho(categories)

    def iter_time_slice_ids(self) -> Iterable[str]:
        """Yield all configured time slice identifiers."""

        for time_slice in self.time_slices:
            yield time_slice.id
