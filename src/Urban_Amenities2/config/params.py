"""Pydantic models describing AUCS 2.0 configuration."""
from __future__ import annotations

from functools import cached_property
from typing import Dict, Iterable, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


class _BaseConfig(BaseModel):
    """Base model that forbids unknown fields and allows reassignment validation."""

    model_config = {
        "extra": "forbid",
        "validate_assignment": True,
    }


class GridConfig(_BaseConfig):
    """Configuration for the spatial grid resolution and search limits."""

    hex_size_m: float = Field(..., gt=0, description="Approximate edge length of the grid in metres")
    isochrone_minutes: List[int] = Field(..., min_length=1, description="Minute values for isochrone rings")
    search_cap_minutes: int = Field(..., gt=0, description="Maximum travel minutes to consider during searches")

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
            getattr(values, field)
            for field in ("EA", "LCA", "MUHAA", "JEA", "MORR", "CTE", "SOU")
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
    max_access_distance_m: Optional[float] = Field(None, gt=0)
    enabled: bool = True

    @cached_property
    def decay_alpha(self) -> float:
        """Continuous-time decay coefficient derived from the half-life."""

        from math import log

        return log(2.0) / self.half_life_min


class NestConfig(_BaseConfig):
    """Grouping of modes for the nested logit."""

    id: str
    modes: List[str] = Field(..., min_length=1)
    mu: float = Field(..., gt=0)
    eta: float = Field(..., gt=0)


class LogitConfig(_BaseConfig):
    """Configuration for the top-level logit."""

    mu_top: float = Field(..., gt=0)


class CarryPenaltyConfig(_BaseConfig):
    """Penalties applied when users have to carry goods."""

    category_multipliers: Dict[str, float]
    per_mode_extra_minutes: Dict[str, float]


class QualityConfig(_BaseConfig):
    """Quality scoring parameters."""

    lambda_weights: Dict[str, float]
    z_clip_abs: float = Field(..., ge=0)
    opening_hours_bonus_xi: float = Field(..., ge=0)
    dedupe_beta_per_km: float = Field(..., ge=0)


class CategoryDiversityConfig(_BaseConfig):
    """Diversity configuration for leisure and essentials."""

    ramp_start: float = Field(..., ge=0)
    ramp_end: float = Field(..., ge=0)
    weight: float = Field(..., ge=0)


class CategoryConfig(_BaseConfig):
    """Category level configuration."""

    essentials: List[str]
    leisure: List[str]
    ces_rho: float
    satiation_mode: Literal["none", "anchor", "direct"] = "none"
    satiation_kappa: Dict[str, float] | float | None = None
    satiation_targets: Optional[Dict[str, Dict[str, float]]] = None
    diversity: Dict[str, CategoryDiversityConfig] = Field(default_factory=dict)

    def derived_satiation(self) -> Dict[str, float]:
        """Compute satiation kappa per category based on the selected mode."""

        from math import log

        if self.satiation_mode == "direct":
            if isinstance(self.satiation_kappa, dict):
                return self.satiation_kappa
            if isinstance(self.satiation_kappa, (int, float)):
                return {name: float(self.satiation_kappa) for name in self.essentials + self.leisure}
            msg = "Direct satiation requires satiation_kappa values"
            raise ValueError(msg)
        if self.satiation_mode == "anchor":
            if not self.satiation_targets:
                msg = "Anchor satiation requires satiation_targets"
                raise ValueError(msg)
            output: Dict[str, float] = {}
            for category, target in self.satiation_targets.items():
                score = target.get("score")
                value = target.get("value")
                if score is None or value is None:
                    msg = f"Missing score/value for satiation target {category}"
                    raise ValueError(msg)
                output[category] = -log(1 - score / 100.0) / value
            return output
        return {}


class LeisureCrossCategoryConfig(_BaseConfig):
    weights: Dict[str, float]
    elasticity_zeta: float
    novelty: Dict[str, float] = Field(default_factory=dict)


class HubsAirportsConfig(_BaseConfig):
    hub_mass_lambda: float
    decay: float
    airport_weights: Dict[str, float]


class JobsEducationConfig(_BaseConfig):
    university_weight_kappa: float
    industry_weights: Dict[str, float]


class MORRConfig(_BaseConfig):
    frequent_exposure: float
    span: float
    reliability: float
    redundancy: float
    micromobility: float


class CorridorConfig(_BaseConfig):
    max_paths: int = Field(..., gt=0)
    stop_buffer_m: float = Field(..., ge=0)
    detour_cap_min: float = Field(..., ge=0)
    pair_categories: List[str] = Field(default_factory=list)
    walk_decay_alpha: float = Field(..., ge=0)


class SeasonalityConfig(_BaseConfig):
    comfort_index_default: float
    weather_adjustments: Dict[str, float] = Field(default_factory=dict)


class NormalizationStandard(_BaseConfig):
    name: str
    percentile: float


class NormalizationConfig(_BaseConfig):
    mode: Literal["metro", "global"] = "metro"
    metro_percentile: float = Field(95.0, ge=0, le=100)
    standards: List[NormalizationStandard] = Field(default_factory=list)


class ComputeConfig(_BaseConfig):
    topK_per_category: int = Field(..., gt=0)
    hub_max_minutes: int = Field(..., gt=0)
    preload_hex_neighbors: bool = True
    cache_dir: Optional[str] = None


class AUCSParams(_BaseConfig):
    """Root configuration object containing all parameters."""

    grid: GridConfig
    subscores: SubscoreWeights
    time_slices: List[TimeSliceConfig]
    modes: Dict[str, ModeConfig]
    nests: List[NestConfig]
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

    def derived_mode_alphas(self) -> Dict[str, float]:
        """Return the decay coefficient per mode."""

        return {mode_name: mode.decay_alpha for mode_name, mode in self.modes.items()}

    def derived_satiation(self) -> Dict[str, float]:
        """Expose derived satiation kappas from the category configuration."""

        return self.categories.derived_satiation()

    def iter_time_slice_ids(self) -> Iterable[str]:
        """Yield all configured time slice identifiers."""

        for time_slice in self.time_slices:
            yield time_slice.id
