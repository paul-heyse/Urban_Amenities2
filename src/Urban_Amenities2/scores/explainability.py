from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import pandas as pd


def _normalize_contribution(entry: Mapping[str, Any]) -> float:
    raw = entry.get("contribution", 0.0)
    try:
        return float(raw) if raw is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


def top_contributors(ea_frame: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for row in ea_frame.itertuples():
        raw_contributors = getattr(row, "contributors", {}) or {}
        if not isinstance(raw_contributors, Mapping):
            continue
        for category, items in raw_contributors.items():
            if not isinstance(items, Sequence):
                continue
            sorted_items = sorted(
                (entry for entry in items if isinstance(entry, Mapping)),
                key=_normalize_contribution,
                reverse=True,
            )[:top_n]
            for item in sorted_items:
                item_dict = dict(item)
                records.append(
                    {
                        "hex_id": getattr(row, "hex_id", None),
                        "category": category,
                        "poi_id": item_dict.get("poi_id"),
                        "name": item_dict.get("name"),
                        "contribution": item_dict.get("contribution"),
                        "quality": item_dict.get("quality"),
                        "quality_components": item_dict.get("quality_components"),
                        "brand_penalty": item_dict.get("brand_penalty"),
                    }
                )
    return pd.DataFrame.from_records(records)


__all__ = ["top_contributors"]
