"""Utilities for loading AUCS parameter configuration from YAML."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError
from ruamel.yaml import YAML

from ..errors import ConfigurationError
from .params import AUCSParams

_yaml = YAML(typ="safe")
_yaml.default_flow_style = False


class ParameterLoadError(ConfigurationError):
    """Raised when configuration files cannot be parsed or validated."""

def _normalise(obj: Any) -> Any:
    """Convert nested Pydantic/complex objects to plain python for hashing."""

    if isinstance(obj, AUCSParams):
        return _normalise(json.loads(obj.model_dump_json()))
    if isinstance(obj, dict):
        return {key: _normalise(value) for key, value in sorted(obj.items())}
    if isinstance(obj, list):
        return [_normalise(value) for value in obj]
    return obj


def compute_param_hash(params: AUCSParams | dict[str, Any]) -> str:
    """Return a deterministic SHA256 hash for the given configuration."""

    normalized = _normalise(params)
    payload = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_params(path: str | Path) -> tuple[AUCSParams, str]:
    """Load a YAML configuration file and return the parsed params and hash."""

    path = Path(path)
    if not path.exists():
        raise ParameterLoadError(f"Parameter file {path} does not exist")

    try:
        data = _yaml.load(path.read_text())
    except Exception as exc:  # pragma: no cover - ruamel provides rich errors
        raise ParameterLoadError(f"Failed to parse YAML: {exc}") from exc

    if not isinstance(data, dict):
        raise ParameterLoadError("Parameter file must define a mapping at the top level")

    try:
        params = AUCSParams.model_validate(data)
    except ValidationError as exc:
        raise ParameterLoadError(str(exc)) from exc

    return params, compute_param_hash(params)


def load_and_document(path: str | Path) -> str:
    """Return a human readable summary of the configuration."""

    params, param_hash = load_params(path)
    lines = ["AUCS Parameters", f"hash: {param_hash}"]
    lines.append("")

    lines.append("Subscore Weights:")
    for name, value in params.subscores.model_dump().items():
        lines.append(f"  - {name}: {value}")

    lines.append("")
    lines.append("Modes:")
    for mode_name, mode in params.modes.items():
        lines.append(
            f"  - {mode_name}: theta_iv={mode.theta_iv}, theta_wait={mode.theta_wait}, alpha={mode.decay_alpha:.4f}"
        )

    lines.append("")
    lines.append("Time slices:")
    for slice_cfg in params.time_slices:
        lines.append(
            f"  - {slice_cfg.id}: weight={slice_cfg.weight}, VOT={slice_cfg.vot_per_hour}"
        )

    derived_satiation = params.derived_satiation()
    if derived_satiation:
        lines.append("")
        lines.append("Derived satiation kappas:")
        for category, value in derived_satiation.items():
            lines.append(f"  - {category}: {value:.4f}")

    return "\n".join(lines)
