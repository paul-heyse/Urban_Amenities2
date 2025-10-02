from __future__ import annotations

import pandas as pd
import pandera.errors
import pytest

from Urban_Amenities2.schemas.scores import CategoryScoreSchema
from Urban_Amenities2.schemas.spatial import POISchema
from Urban_Amenities2.schemas.travel import TravelTimeSkimSchema
from Urban_Amenities2.schemas.utils import validate_with_schema


def test_poi_schema_valid() -> None:
    frame = pd.DataFrame(
        {
            "poi_id": ["1"],
            "hex_id": ["8928308281bffff"],
            "aucstype": ["groceries"],
            "name": ["Fresh Mart"],
            "brand": [None],
            "lat": [39.7392],
            "lon": [-104.9903],
            "quality_attrs": [{}],
        }
    )
    POISchema.validate(frame)


def test_travel_time_validation_error() -> None:
    frame = pd.DataFrame(
        {
            "origin_hex": ["a"],
            "dest_hex": ["b"],
            "mode": ["walk"],
            "period": ["am"],
            "duration_min": [-1],
            "distance_m": [100],
            "ok": [True],
        }
    )
    with pytest.raises(pandera.errors.SchemaError):
        TravelTimeSkimSchema.validate(frame)


def test_category_score_schema() -> None:
    frame = pd.DataFrame(
        {
            "hex_id": ["a"],
            "category": ["groceries"],
            "raw_score": [12.5],
            "normalized_score": [90.0],
        }
    )
    CategoryScoreSchema.validate(frame)


def test_validation_decorator() -> None:
    frame = pd.DataFrame(
        {
            "poi_id": ["1"],
            "hex_id": ["8928308281bffff"],
            "aucstype": ["groceries"],
            "name": ["Fresh Mart"],
            "brand": [None],
            "lat": [39.7392],
            "lon": [-104.9903],
            "quality_attrs": [{}],
        }
    )

    @validate_with_schema(POISchema)
    def passthrough(df: pd.DataFrame) -> pd.DataFrame:
        return df

    result = passthrough(frame)
    assert result.equals(frame)
