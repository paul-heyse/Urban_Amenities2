from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from ..logging_utils import get_logger

LOGGER = get_logger("aucs.export.parquet")


def write_scores(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(path)
    LOGGER.info("scores_written", path=str(path), rows=len(frame))


def write_explainability(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(path)
    LOGGER.info("explainability_written", path=str(path), rows=len(frame))


def summary_statistics(frame: pd.DataFrame, score_column: str = "aucs") -> dict[str, float]:
    series = frame[score_column]
    return {
        "min": float(series.min()),
        "max": float(series.max()),
        "mean": float(series.mean()),
        "median": float(series.median()),
        "p5": float(series.quantile(0.05)),
        "p95": float(series.quantile(0.95)),
        "generated_at": datetime.now(UTC).isoformat(),
    }


__all__ = ["write_scores", "write_explainability", "summary_statistics"]
