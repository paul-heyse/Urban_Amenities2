"""Pandera schemas for travel time and itinerary datasets."""

from __future__ import annotations

import pandera as pa
from pandera import Check, Column, DataFrameSchema

TravelTimeSkimSchema = DataFrameSchema(
    {
        "origin_hex": Column(pa.String),
        "dest_hex": Column(pa.String),
        "mode": Column(pa.String),
        "period": Column(pa.String),
        "duration_min": Column(pa.Float, Check.ge(0)),
        "distance_m": Column(pa.Float, Check.ge(0)),
        "ok": Column(pa.Bool),
    },
    coerce=True,
    strict=True,
)


TransitItinerarySchema = DataFrameSchema(
    {
        "origin_hex": Column(pa.String),
        "dest_hex": Column(pa.String),
        "period": Column(pa.String),
        "walk_time": Column(pa.Float, Check.ge(0)),
        "transit_time": Column(pa.Float, Check.ge(0)),
        "wait_time": Column(pa.Float, Check.ge(0)),
        "transfers": Column(pa.Int, Check.ge(0)),
        "fare_usd": Column(pa.Float, Check.ge(0)),
    },
    coerce=True,
    strict=True,
)
