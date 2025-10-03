"""Pandera schemas describing AUCS scoring outputs."""

from __future__ import annotations

import pandera as pa
from pandera import Check, Column, DataFrameSchema

CategoryScoreSchema = DataFrameSchema(
    {
        "hex_id": Column(pa.String),
        "category": Column(pa.String),
        "raw_score": Column(pa.Float),
        "normalized_score": Column(pa.Float, Check.in_range(0, 100)),
    },
    coerce=True,
    strict=True,
)


SubscoreSchema = DataFrameSchema(
    {
        "hex_id": Column(pa.String),
        "subscore_name": Column(pa.String),
        "value": Column(pa.Float),
        "contributors": Column(pa.Object),
    },
    coerce=True,
    strict=True,
)


FinalScoreSchema = DataFrameSchema(
    {
        "hex_id": Column(pa.String),
        "aucs": Column(pa.Float, Check.in_range(0, 100)),
        "subscores_dict": Column(pa.Object),
        "metadata": Column(pa.Object),
    },
    coerce=True,
    strict=True,
)


EAOutputSchema = DataFrameSchema(
    {
        "hex_id": Column(pa.String),
        "EA": Column(pa.Float, Check.in_range(0, 100)),
        "penalty": Column(pa.Float, Check.ge(0)),
        "category_scores": Column(pa.Object),
        "contributors": Column(pa.Object),
    },
    coerce=True,
    strict=True,
)
