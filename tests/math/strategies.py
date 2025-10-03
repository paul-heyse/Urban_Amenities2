"""Shared Hypothesis strategies for math module tests."""

from __future__ import annotations

from hypothesis import strategies as st

positive_floats = st.floats(
    min_value=1e-6,
    max_value=1e6,
    allow_nan=False,
    allow_infinity=False,
)

elasticity_params = st.floats(
    min_value=-5.0,
    max_value=10.0,
    allow_nan=False,
    allow_infinity=False,
)

ces_inputs = st.lists(positive_floats, min_size=2, max_size=20)

satiation_lambdas = st.floats(
    min_value=0.01,
    max_value=10.0,
    allow_nan=False,
    allow_infinity=False,
)

amenity_counts = st.integers(min_value=1, max_value=1000)

diversity_counts = st.lists(positive_floats, min_size=1, max_size=15)

scale_factors = st.floats(min_value=0.5, max_value=5.0, allow_nan=False, allow_infinity=False)
