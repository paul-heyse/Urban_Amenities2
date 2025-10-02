"""Parameter adjustment interface for AUCS model."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

import structlog

from Urban_Amenities2.config.params import AUCSParams

logger = structlog.get_logger()


@dataclass
class ParameterDiff:
    """Track changes to parameters."""

    original: dict[str, float]
    modified: dict[str, float]
    changed_keys: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Identify changed parameters."""
        self.changed_keys = [
            key for key in self.modified if self.original.get(key) != self.modified.get(key)
        ]

    def has_changes(self) -> bool:
        """Check if any parameters have changed."""
        return len(self.changed_keys) > 0


class ParameterAdjuster:
    """Manage parameter adjustments in the UI."""

    def __init__(self, params: AUCSParams):
        """
        Initialize parameter adjuster.

        Args:
            params: Base AUCS parameters
        """
        self.params = params
        self.original_params = self._extract_adjustable_params()
        self.modified_params = self.original_params.copy()

    def _extract_adjustable_params(self) -> dict[str, float]:
        """Extract parameters that can be adjusted in the UI."""
        adjustable = {}

        # Subscore weights
        adjustable["weight_ea"] = self.params.weights.ea
        adjustable["weight_lca"] = self.params.weights.lca
        adjustable["weight_muhaa"] = self.params.weights.muhaa
        adjustable["weight_jea"] = self.params.weights.jea
        adjustable["weight_morr"] = self.params.weights.morr
        adjustable["weight_cte"] = self.params.weights.cte
        adjustable["weight_sou"] = self.params.weights.sou

        # Decay parameters (mode-specific)
        adjustable["alpha_walk"] = self.params.modes.walk.alpha
        adjustable["alpha_bike"] = self.params.modes.bike.alpha
        adjustable["alpha_transit"] = self.params.modes.transit.alpha
        adjustable["alpha_car"] = self.params.modes.car.alpha

        # Value of time
        adjustable["vot_weekday"] = self.params.gtc.vot_weekday
        adjustable["vot_weekend"] = self.params.gtc.vot_weekend

        return adjustable

    def update_parameter(self, key: str, value: float) -> None:
        """
        Update a single parameter.

        Args:
            key: Parameter key (e.g., 'weight_ea', 'alpha_walk')
            value: New parameter value
        """
        if key not in self.original_params:
            logger.warning("unknown_parameter", key=key)
            return

        self.modified_params[key] = value
        logger.info("parameter_updated", key=key, value=value)

    def get_diff(self) -> ParameterDiff:
        """Get diff between original and modified parameters."""
        return ParameterDiff(original=self.original_params, modified=self.modified_params)

    def validate_weights(self) -> tuple[bool, str]:
        """
        Validate that subscore weights sum to 100.

        Returns:
            Tuple of (is_valid, error_message)
        """
        weight_keys = [f"weight_{s}" for s in ["ea", "lca", "muhaa", "jea", "morr", "cte", "sou"]]
        weight_sum = sum(self.modified_params[k] for k in weight_keys)

        if abs(weight_sum - 100.0) > 0.01:
            return False, f"Weights sum to {weight_sum:.2f}, must equal 100.0"

        return True, ""

    def reset(self) -> None:
        """Reset all parameters to original values."""
        self.modified_params = self.original_params.copy()
        logger.info("parameters_reset")

    def to_dict(self) -> dict[str, float]:
        """Export modified parameters as dictionary."""
        return self.modified_params.copy()

