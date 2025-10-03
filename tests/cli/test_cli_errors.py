from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from Urban_Amenities2.cli.main import app


def test_missing_required_argument(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(app, ["score", "ea"])
    assert result.exit_code == 2
    assert "Missing argument" in result.output


def test_aggregate_invalid_path(cli_runner: CliRunner, tmp_path: Path) -> None:
    weights = tmp_path / "weights.json"
    weights.write_text("{}", encoding="utf-8")
    missing = tmp_path / "missing.csv"
    result = cli_runner.invoke(app, ["aggregate", str(missing), "--weights", str(weights)])
    assert result.exit_code == 1
    assert "File not found" in result.output


def test_aggregate_invalid_weights(cli_runner: CliRunner, tmp_path: Path) -> None:
    subscores = tmp_path / "subscores.csv"
    subscores.write_text("hex_id,EA\nabc,1\n", encoding="utf-8")
    result = cli_runner.invoke(app, ["aggregate", str(subscores), "--weights", "not-json"])
    assert result.exit_code != 0
    assert isinstance(result.exception, json.JSONDecodeError)


def test_export_invalid_format(cli_runner: CliRunner, tmp_path: Path) -> None:
    scores = tmp_path / "scores.csv"
    scores.write_text("hex_id,aucs\nabc,1\n", encoding="utf-8")
    result = cli_runner.invoke(
        app,
        ["export", str(tmp_path / "out.txt"), "--format", "csv", "--scores", str(scores)],
    )
    assert result.exit_code == 1
    assert "Unsupported export format" in result.output
