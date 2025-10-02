from __future__ import annotations

import numpy as np


def compute_kappa_from_anchor(target_score: float, target_value: float) -> float:
    if target_value <= 0:
        raise ValueError("target_value must be positive")
    if not (0 < target_score < 100):
        raise ValueError("target_score must be between 0 and 100")
    return -np.log(1 - target_score / 100.0) / target_value


def apply_satiation(values: np.ndarray, kappa: np.ndarray | float) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    kappa = np.asarray(kappa, dtype=float)
    return 100.0 * (1.0 - np.exp(-kappa * values))


def resolve_kappa(kappa: float | dict[str, float], anchors: dict[str, tuple[float, float]] | None = None) -> dict[str, float]:
    resolved: dict[str, float] = {}
    if isinstance(kappa, dict):
        resolved.update(kappa)
    elif isinstance(kappa, (float, int)):
        resolved = {"default": float(kappa)}
    else:
        raise TypeError("kappa must be float or dict")
    if anchors:
        for key, (target_score, target_value) in anchors.items():
            resolved[key] = compute_kappa_from_anchor(target_score, target_value)
    return resolved


__all__ = ["apply_satiation", "compute_kappa_from_anchor", "resolve_kappa"]
