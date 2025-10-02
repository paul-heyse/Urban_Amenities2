"""Pandera schemas for spatial datasets."""
from __future__ import annotations

import pandera as pa
from pandera import Check, Column, DataFrameSchema

HexIndexSchema = DataFrameSchema(
    {
        "hex_id": Column(pa.String, nullable=False),
        "centroid_lat": Column(pa.Float, Check.in_range(-90, 90)),
        "centroid_lon": Column(pa.Float, Check.in_range(-180, 180)),
        "geometry": Column(pa.Object, nullable=False),
    },
    coerce=True,
    strict=True,
)


POISchema = DataFrameSchema(
    {
        "poi_id": Column(pa.String),
        "hex_id": Column(pa.String),
        "aucstype": Column(pa.String),
        "name": Column(pa.String, nullable=True),
        "brand": Column(pa.String, nullable=True),
        "lat": Column(pa.Float, Check.in_range(-90, 90)),
        "lon": Column(pa.Float, Check.in_range(-180, 180)),
        "quality_attrs": Column(pa.Object, nullable=True),
        "quality": Column(pa.Float, Check.in_range(0, 100)),
        "quality_base": Column(pa.Float, Check.in_range(0, 100), nullable=True),
        "quality_size": Column(pa.Float, Check.in_range(0, 100), nullable=True),
        "quality_popularity": Column(pa.Float, Check.in_range(0, 100), nullable=True),
        "quality_brand": Column(pa.Float, Check.in_range(0, 100), nullable=True),
        "quality_heritage": Column(pa.Float, Check.in_range(0, 100), nullable=True),
        "quality_hours_category": Column(pa.String, nullable=True),
        "quality_hours_bonus": Column(pa.Float, nullable=True),
        "quality_components": Column(pa.Object, nullable=True),
        "brand_penalty": Column(pa.Float, Check.in_range(0, 1), nullable=True),
        "brand_weight": Column(pa.Float, Check.ge(0), nullable=True),
    },
    coerce=True,
    strict=True,
)


NetworkSegmentSchema = DataFrameSchema(
    {
        "segment_id": Column(pa.String),
        "hex_id": Column(pa.String),
        "geometry": Column(pa.Object),
        "mode_flags": Column(pa.Object),
        "speed": Column(pa.Float, Check.gt(0)),
    },
    coerce=True,
    strict=True,
)
