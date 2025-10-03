from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(slots=True)
class GTCParameters:
    theta_iv: float
    theta_wait: float
    theta_walk: float
    transfer_penalty: float
    reliability_weight: float
    value_of_time: float
    carry_penalty: float = 0.0


def generalized_travel_cost(
    in_vehicle: NDArray[np.float64],
    wait: NDArray[np.float64],
    walk: NDArray[np.float64],
    transfers: NDArray[np.float64],
    reliability: NDArray[np.float64],
    fare: NDArray[np.float64],
    params: GTCParameters,
    carry_adjustment: NDArray[np.float64] | float = 0.0,
) -> NDArray[np.float64]:
    denominator = params.value_of_time if params.value_of_time > 0 else 1.0
    fare_component = np.divide(
        fare,
        denominator,
        out=np.zeros_like(fare, dtype=float),
    ).astype(float)
    result = (
        params.theta_iv * in_vehicle
        + params.theta_wait * wait
        + params.theta_walk * walk
        + params.transfer_penalty * transfers
        + params.reliability_weight * reliability
        + fare_component
        + params.carry_penalty
    )
    adjustment = np.asarray(carry_adjustment, dtype=float)
    return np.asarray(result + adjustment, dtype=float)


__all__ = ["generalized_travel_cost", "GTCParameters"]
