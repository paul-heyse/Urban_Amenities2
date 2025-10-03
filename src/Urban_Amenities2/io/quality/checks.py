from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

import pandas as pd


def coverage_check(pois: pd.DataFrame, hex_col: str = "hex_id") -> dict[str, float]:
    counts = pois.groupby(hex_col).size()
    return {
        "hex_count": int(counts.size),
        "avg_pois_per_hex": float(counts.mean()) if not counts.empty else 0.0,
    }


def completeness_check(pois: pd.DataFrame, required_columns: Iterable[str]) -> dict[str, float]:
    metrics: dict[str, float] = {}
    for column in required_columns:
        metrics[column] = float(pois[column].notna().mean()) if column in pois.columns else 0.0
    return metrics


def validity_check(
    pois: pd.DataFrame, lat_col: str = "lat", lon_col: str = "lon"
) -> dict[str, float]:
    if pois.empty:
        return {"within_bounds": 1.0}
    within = ((pois[lat_col].between(-90, 90)) & (pois[lon_col].between(-180, 180))).mean()
    return {"within_bounds": float(within)}


def consistency_check(
    pois: pd.DataFrame, enrichment: pd.DataFrame | None = None
) -> dict[str, float]:
    metrics: dict[str, float] = {
        "dedupe_weight_non_null": float(
            pois.get("dedupe_weight", pd.Series([1], dtype=float)).notna().mean()
        )
    }
    if enrichment is not None and "poi_id" in pois.columns and "poi_id" in enrichment.columns:
        joined = pois.merge(enrichment, on="poi_id", how="left", indicator=True)
        metrics["enrichment_join_rate"] = float((joined["_merge"] == "both").mean())
    return metrics


def generate_report(
    pois: pd.DataFrame,
    output_dir: Path = Path("data/quality_reports"),
    enrichment: pd.DataFrame | None = None,
) -> dict[str, dict[str, float]]:
    report = {
        "coverage": coverage_check(pois),
        "completeness": completeness_check(pois, ["name", "aucstype", "hex_id"]),
        "validity": validity_check(pois),
        "consistency": consistency_check(pois, enrichment=enrichment),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "pois_quality.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


__all__ = [
    "coverage_check",
    "completeness_check",
    "validity_check",
    "consistency_check",
    "generate_report",
]
