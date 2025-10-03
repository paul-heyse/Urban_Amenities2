from __future__ import annotations

import pandas as pd

from Urban_Amenities2.config.loader import load_params
from Urban_Amenities2.schemas.spatial import POISchema


def test_parameter_to_schema_pipeline() -> None:
    params, _ = load_params("configs/params_default.yml")
    poi_frame = pd.DataFrame(
        {
            "poi_id": ["1"],
            "hex_id": ["8928308281bffff"],
            "aucstype": [params.categories.essentials[0]],
            "name": ["Fresh Mart"],
            "brand": [None],
            "lat": [39.7392],
            "lon": [-104.9903],
            "quality_attrs": [{}],
            "quality": [75.0],
            "quality_base": [70.0],
            "quality_size": [65.0],
            "quality_popularity": [80.0],
            "quality_brand": [50.0],
            "quality_heritage": [60.0],
            "quality_hours_category": ["standard"],
            "quality_hours_bonus": [0.0],
            "quality_components": [
                [{"size": 65.0, "popularity": 80.0, "brand": 50.0, "heritage": 60.0}]
            ],
            "brand_penalty": [1.0],
            "brand_weight": [1.0],
        }
    )
    validated = POISchema.validate(poi_frame)
    assert validated["aucstype"].iloc[0] == params.categories.essentials[0]
