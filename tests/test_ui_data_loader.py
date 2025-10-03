from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import pytest

from Urban_Amenities2.ui.config import UISettings
from Urban_Amenities2.ui.data_loader import DataContext


@pytest.fixture
def score_frame() -> pd.DataFrame:
    data = {
        "hex_id": ["8928308280fffff"],
        "aucs": [75.0],
        "EA": [80.0],
        "LCA": [70.0],
        "MUHAA": [65.0],
        "JEA": [85.0],
        "MORR": [75.0],
        "CTE": [60.0],
        "SOU": [70.0],
        "state": ["CO"],
        "metro": ["Denver"],
        "county": ["Denver"],
    }
    frame = pd.DataFrame(data)
    frame["hex_id"] = frame["hex_id"].astype(str)
    return frame


def test_data_context_prefers_score_files(tmp_path: Path, score_frame: pd.DataFrame) -> None:
    data_dir = tmp_path / "ui-data"
    data_dir.mkdir()

    scores_path = data_dir / "20240101_scores.parquet"
    score_frame.to_parquet(scores_path)

    metadata = score_frame[["hex_id", "state", "metro", "county"]].copy()
    metadata_path = data_dir / "metadata.parquet"
    metadata.to_parquet(metadata_path)

    # Make metadata appear newer than the score file to mirror production ordering
    newer_mtime = scores_path.stat().st_mtime + 5
    os.utime(metadata_path, (newer_mtime, newer_mtime))

    settings = UISettings(data_path=data_dir)
    context = DataContext.from_settings(settings)

    assert context.version is not None
    assert context.version.path == scores_path
    assert not context.scores.empty
    required_columns = {"EA", "LCA", "MUHAA", "JEA", "MORR", "CTE", "SOU"}
    assert required_columns.issubset(context.scores.columns)


def test_data_context_handles_missing_scores(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    data_dir = tmp_path / "ui-empty"
    data_dir.mkdir()

    metadata = pd.DataFrame(
        {
            "hex_id": [],
            "state": [],
            "metro": [],
            "county": [],
        }
    )
    metadata.to_parquet(data_dir / "metadata.parquet")

    settings = UISettings(data_path=data_dir)
    with caplog.at_level("WARNING", logger="ui.data"):
        context = DataContext.from_settings(settings)

    assert any("ui_scores_missing" in record.message for record in caplog.records)
    assert context.version is None
    assert context.scores.empty
    assert context.metadata.empty
