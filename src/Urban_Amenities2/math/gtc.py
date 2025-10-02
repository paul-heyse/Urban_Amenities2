from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class GTCParameters:
    theta_iv: float
    theta_wait: float
    theta_walk: float
    transfer_penalty: float
    reliability_weight: float
    value_of_time: float
    carry_penalty: float = 0.0


def generalized_travel_cost(
    in_vehicle: np.ndarray,
    wait: np.ndarray,
    walk: np.ndarray,
    transfers: np.ndarray,
    reliability: np.ndarray,
    fare: np.ndarray,
    params: GTCParameters,
    carry_adjustment: np.ndarray | float = 0.0,
) -> np.ndarray:
    fare_component = np.divide(fare, params.value_of_time, out=np.zeros_like(fare, dtype=float), where=params.value_of_time > 0)
    result = (
        params.theta_iv * in_vehicle
        + params.theta_wait * wait
        + params.theta_walk * walk
        + params.transfer_penalty * transfers
        + params.reliability_weight * reliability
        + fare_component
        + params.carry_penalty
    )
    return result + carry_adjustment


__all__ = ["generalized_travel_cost", "GTCParameters"]
