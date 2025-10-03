from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from ..scores.essentials_access import EssentialsAccessCalculator, EssentialsAccessConfig


def sensitivity_analysis(
    calculator: EssentialsAccessCalculator,
    pois: pd.DataFrame,
    accessibility: pd.DataFrame,
    parameter: str,
    values: Iterable[float],
) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for value in values:
        _apply_parameter(calculator.config, parameter, value)
        ea, _ = calculator.compute(pois, accessibility)
        records.append({"parameter": parameter, "value": value, "ea_mean": ea["EA"].mean()})
    return pd.DataFrame.from_records(records)


def _apply_parameter(config: EssentialsAccessConfig, parameter: str, value: float) -> None:
    if parameter.startswith("rho:"):
        category = parameter.split(":", 1)[1]
        params = config.category_params.get(category)
        if params:
            params.rho = value
    elif parameter.startswith("kappa:"):
        category = parameter.split(":", 1)[1]
        params = config.category_params.get(category)
        if params:
            params.kappa = value
    elif parameter.startswith("diversity_weight:"):
        category = parameter.split(":", 1)[1]
        params = config.category_params.get(category)
        if params:
            params.diversity.weight = value
    else:
        raise ValueError(f"Unknown parameter {parameter}")


__all__ = ["sensitivity_analysis"]
