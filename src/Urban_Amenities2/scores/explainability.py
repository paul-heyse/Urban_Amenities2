from __future__ import annotations

import pandas as pd


def top_contributors(ea_frame: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for row in ea_frame.itertuples():
        contributors: dict[str, list[dict[str, object]]] = getattr(row, "contributors", {}) or {}
        # Handle None or empty contributors
        if not contributors:
            continue
        for category, items in contributors.items():
            # Handle None items list
            if not items:
                continue
            for item in sorted(items, key=lambda entry: entry.get("contribution", 0), reverse=True)[:top_n]:
                records.append(
                    {
                        "hex_id": row.hex_id,
                        "category": category,
                        "poi_id": item.get("poi_id"),
                        "name": item.get("name"),
                        "contribution": item.get("contribution"),
                        "quality": item.get("quality"),
                        "quality_components": item.get("quality_components"),
                        "brand_penalty": item.get("brand_penalty"),
                    }
                )
    return pd.DataFrame.from_records(records)


__all__ = ["top_contributors"]
