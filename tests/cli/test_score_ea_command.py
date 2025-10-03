from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from typer.testing import CliRunner

from Urban_Amenities2.cli.main import app


@pytest.fixture()
def cli_runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def sample_ea_inputs(tmp_path: Path) -> tuple[Path, Path]:
    resources = Path("tests/cli/resources")
    pois_path = resources / "ea_pois.parquet"
    accessibility_path = resources / "ea_access.parquet"
    temp_pois = tmp_path / "pois.parquet"
    temp_access = tmp_path / "accessibility.parquet"
    pd.read_parquet(pois_path).to_parquet(temp_pois)
    pd.read_parquet(accessibility_path).to_parquet(temp_access)
    return temp_pois, temp_access


def test_score_ea_generates_outputs(cli_runner: CliRunner, sample_ea_inputs: tuple[Path, Path]) -> None:
    pois_path, accessibility_path = sample_ea_inputs
    output_path = pois_path.parent / "ea_scores.parquet"
    category_path = pois_path.parent / "ea_category.parquet"

    result = cli_runner.invoke(
        app,
        [
            "score",
            "ea",
            str(pois_path),
            str(accessibility_path),
            "--output",
            str(output_path),
            "--category-output",
            str(category_path),
        ],
    )

    assert result.exit_code == 0
    assert output_path.exists()
    assert category_path.exists()

    scores = pd.read_parquet(output_path)
    categories = pd.read_parquet(category_path)

    assert {"hex_id", "EA", "penalty"}.issubset(scores.columns)
    assert {"hex_id", "category", "score"}.issubset(categories.columns)

    assert scores["EA"].between(0, 100).all()
    expected_hex_scores = {
        "hex1": pytest.approx(100.0),
        "hex2": pytest.approx(95.92377960216338),
    }
    for hex_id, expected_value in expected_hex_scores.items():
        actual = scores.loc[scores["hex_id"] == hex_id, "EA"].iloc[0]
        assert actual == expected_value
    assert categories.groupby("hex_id")["score"].sum().ge(0).all()


