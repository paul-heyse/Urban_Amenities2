"""Regression fixtures for math module testing."""

from __future__ import annotations

import math

CES_REGRESSION_VECTORS: list[
    tuple[list[float], list[float], float, float, float]
] = [
    (
        [1.0, 1.0, 1.0],
        [10.0, 20.0, 30.0],
        2.0,
        math.sqrt(10.0**2 + 20.0**2 + 30.0**2),
        1e-9,
    ),
    (
        [1.0, 1.0, 1.0],
        [5.0, 5.0, 5.0],
        1.0,
        15.0,
        1e-12,
    ),
    (
        [1.0, 1.0, 1.0],
        [100.0, 1.0, 1.0],
        0.5,
        144.0,
        1e-9,
    ),
]

SATIATION_REGRESSION_VECTORS: list[tuple[int, float, float, float, float]] = [
    (1, 1.0, 1.0 - math.exp(-1.0), 1e-9, 0.0),
    (5, 0.5, (1.0 - math.exp(-0.5 * 5.0)) / 5.0, 1e-9, 1e-12),
    (10, 2.0, (1.0 - math.exp(-2.0 * 10.0)) / 10.0, 1e-9, 1e-12),
]

DIVERSITY_REGRESSION_VECTORS: list[tuple[list[float], float]] = [
    ([10.0, 10.0, 10.0, 10.0], math.log(4.0)),
    ([100.0, 1.0, 1.0, 1.0], 0.16368997270721694),
    ([50.0], 0.0),
]
