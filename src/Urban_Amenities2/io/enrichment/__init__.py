from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import pandas as pd


def merge_enrichment(
    pois: pd.DataFrame,
    wikidata: Optional[pd.DataFrame] = None,
    wikipedia: Optional[pd.DataFrame] = None,
    output_path: Path | None = None,
) -> pd.DataFrame:
    frame = pois.copy()
    if wikidata is not None:
        frame = frame.merge(wikidata, on="poi_id", how="left")
        frame["brand_wd"] = frame["wikidata_qid"]
    if wikipedia is not None:
        frame = frame.merge(wikipedia[["poi_id", "median_views", "popularity_z", "iqr"]], on="poi_id", how="left")
    frame["quality_attrs"] = frame.apply(_build_quality_attrs, axis=1)
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(output_path)
    return frame


def _build_quality_attrs(row: pd.Series) -> str:
    attrs = {}
    for key in ("capacity", "heritage_status", "median_views", "popularity_z", "iqr"):
        value = row.get(key)
        if pd.notna(value):
            attrs[key] = value
    return json.dumps(attrs, sort_keys=True)


__all__ = ["merge_enrichment"]
