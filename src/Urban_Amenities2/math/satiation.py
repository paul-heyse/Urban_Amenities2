from __future__ import annotations

from __future__ import annotations

from typing import Dict

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
    if np.any(kappa <= 0):
        raise ValueError("kappa must be positive")
    scores = 100.0 * (1.0 - np.exp(-kappa * values))
    return np.clip(scores, 0.0, 100.0)


def resolve_kappa(
    kappa: float | dict[str, float] | None,
    anchors: dict[str, tuple[float, float]] | None = None,
) -> Dict[str, float]:
    resolved: Dict[str, float] = {}
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
