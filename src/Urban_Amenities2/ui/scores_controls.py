"""Shared constants for score controls."""

from __future__ import annotations

from typing import Mapping

from .types import DropdownOption


SUBSCORE_OPTIONS: list[DropdownOption] = [
    {"label": "Total AUCS", "value": "aucs"},
    {"label": "Essentials Access", "value": "EA"},
    {"label": "Leisure & Culture", "value": "LCA"},
    {"label": "Major Urban Hub & Airport Access", "value": "MUHAA"},
    {"label": "Jobs & Education", "value": "JEA"},
    {"label": "Mobility Reliability", "value": "MORR"},
    {"label": "Corridor Trip Enrichment", "value": "CTE"},
    {"label": "Seasonal Outdoors", "value": "SOU"},
]

SUBSCORE_DESCRIPTIONS: Mapping[str, str] = {
    "aucs": "Overall composite score aggregating all subscores with current weights.",
    "EA": "Access to essential amenities such as groceries, pharmacies, and childcare.",
    "LCA": "Leisure and culture opportunities including dining, arts, parks, and recreation.",
    "MUHAA": "Connectivity to major urban hubs and airports weighted by travel cost.",
    "JEA": "Jobs and education accessibility capturing employment centers and universities.",
    "MORR": "Mobility options, reliability, and resilience across transit and micromobility.",
    "CTE": "Corridor trip-chaining enrichment measuring errand-friendly transit paths.",
    "SOU": "Seasonal outdoors comfort balancing climate, trails, and recreation readiness.",
}


__all__ = ["SUBSCORE_OPTIONS", "SUBSCORE_DESCRIPTIONS"]
