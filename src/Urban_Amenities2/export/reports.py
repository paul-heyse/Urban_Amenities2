from __future__ import annotations

from pathlib import Path
from typing import Dict

import pandas as pd

from .parquet import summary_statistics


def build_report(scores: pd.DataFrame, subscores: pd.DataFrame, path: Path) -> Dict[str, float]:
    stats = summary_statistics(scores, score_column="aucs")
    path.parent.mkdir(parents=True, exist_ok=True)
    html = ["<html><head><title>AUCS QA Report</title></head><body>"]
    html.append("<h1>AUCS Summary</h1>")
    html.append(pd.DataFrame([stats]).to_html(index=False))
    html.append("<h2>Subscore Correlations</h2>")
    numeric = subscores.select_dtypes(include=["number"])
    correlations = numeric.corr()
    html.append(correlations.to_html())
    html.append("</body></html>")
    path.write_text("\n".join(html), encoding="utf-8")
    return stats


__all__ = ["build_report"]
