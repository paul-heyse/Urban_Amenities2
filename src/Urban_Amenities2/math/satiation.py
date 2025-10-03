from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def compute_kappa_from_anchor(target_score: float, target_value: float) -> float:
    if target_value <= 0:
        raise ValueError("target_value must be positive")
    if not (0 < target_score < 100):
        raise ValueError("target_score must be between 0 and 100")
    result = -np.log(1 - target_score / 100.0) / target_value
    return float(result)


def apply_satiation(
    values: NDArray[np.float64] | float,
    kappa: NDArray[np.float64] | float,
) -> NDArray[np.float64]:
    values_array = np.asarray(values, dtype=float)
    kappa_array = np.asarray(kappa, dtype=float)
    if np.any(kappa_array <= 0):
        raise ValueError("kappa must be positive")
    scores = 100.0 * (1.0 - np.exp(-kappa_array * values_array))
    clipped = np.clip(scores, 0.0, 100.0)
    return np.asarray(clipped, dtype=float)


def resolve_kappa(
    kappa: float | dict[str, float] | None,
    anchors: dict[str, tuple[float, float]] | None = None,
) -> dict[str, float]:
    resolved: dict[str, float] = {}
    if isinstance(kappa, dict):
        for key, value in kappa.items():
            if value <= 0:
                raise ValueError("kappa values must be positive")
            resolved[key] = float(value)
    elif isinstance(kappa, (float, int)):
        if kappa <= 0:
            raise ValueError("kappa must be positive")
        resolved = {"default": float(kappa)}
    elif kappa is not None:
        raise TypeError("kappa must be float, dict, or None")
    if anchors:
        for key, (target_score, target_value) in anchors.items():
            resolved[key] = compute_kappa_from_anchor(target_score, target_value)
    return resolved


__all__ = ["apply_satiation", "compute_kappa_from_anchor", "resolve_kappa"]
