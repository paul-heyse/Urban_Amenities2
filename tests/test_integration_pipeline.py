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
        }
    )
    validated = POISchema.validate(poi_frame)
    assert validated["aucstype"].iloc[0] == params.categories.essentials[0]
