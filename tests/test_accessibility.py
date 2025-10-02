import pandas as pd

from Urban_Amenities2.accessibility.matrices import (
    AccessibilityConfig,
    AccessibilityMatrixBuilder,
    NestConfig,
)
from Urban_Amenities2.math.logsum import ModeUtilityParams


def test_accessibility_matrix_builder() -> None:
    frame = pd.DataFrame(
        {
            "origin_hex": ["hex1", "hex1"],
            "poi_id": ["poi1", "poi1"],
            "mode": ["car", "bike"],
            "period": ["AM", "AM"],
            "gtc": [20.0, 30.0],
            "comfort": [0.1, 0.2],
        }
    )

    config = AccessibilityConfig(
        mode_params={
            "car": ModeUtilityParams(beta0=1.0, alpha=0.05, comfort_weight=0.1),
            "bike": ModeUtilityParams(beta0=0.5, alpha=0.08, comfort_weight=0.2),
        },
        nests={
            "auto": NestConfig(modes=["car"], mu=0.7),
            "active": NestConfig(modes=["bike"], mu=0.9),
        },
        mu_top=1.0,
        time_weights=[0.6, 0.4],
    )

    builder = AccessibilityMatrixBuilder(config)
    result = builder.build(frame)
    assert set(result.columns) == {"origin_hex", "poi_id", "weight", "inclusive_value"}
    assert (result["weight"] >= 0).all()
    assert result.loc[0, "inclusive_value"] != 0
