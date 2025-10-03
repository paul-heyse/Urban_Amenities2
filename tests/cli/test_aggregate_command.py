from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import pytest
from pytest import MonkeyPatch
from typer.testing import CliRunner

from Urban_Amenities2.cli.main import app


def _write_subscores(path: Path) -> None:
    frame = pd.DataFrame({"hex_id": ["abc"], "EA": [10.0], "LCA": [20.0]})
    frame.to_csv(path, index=False)


def _write_weights(path: Path) -> None:
    payload = {"EA": 0.5, "LCA": 0.5}
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_aggregate_command_writes_scores(
    cli_runner: CliRunner, tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    subscores = tmp_path / "subscores.csv"
    _write_subscores(subscores)
    weights = tmp_path / "weights.json"
    _write_weights(weights)
    output = tmp_path / "output.parquet"
    calls: dict[str, Path] = {}

    def fake_write_scores(frame: pd.DataFrame, path: Path) -> None:
        calls["path"] = path
        path.write_text("scores", encoding="utf-8")

    monkeypatch.setattr("Urban_Amenities2.cli.main.write_scores", fake_write_scores)

    result = cli_runner.invoke(
        app,
        ["aggregate", str(subscores), "--weights", str(weights), "--output", str(output)],
    )

    assert result.exit_code == 0
    assert "Wrote AUCS scores" in result.output
    assert calls["path"] == output
    assert output.exists()


def test_aggregate_command_handles_missing_file(cli_runner: CliRunner, tmp_path: Path) -> None:
    weights = tmp_path / "weights.json"
    _write_weights(weights)
    missing = tmp_path / "missing.csv"
    result = cli_runner.invoke(app, ["aggregate", str(missing), "--weights", str(weights)])
    assert result.exit_code == 1
    assert "File not found" in result.output


def test_aggregate_command_keyboard_interrupt(
    cli_runner: CliRunner, tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    subscores = tmp_path / "subscores.csv"
    _write_subscores(subscores)
    weights = tmp_path / "weights.json"
    _write_weights(weights)

    def boom(*args: object, **kwargs: object) -> pd.DataFrame:
        raise KeyboardInterrupt

    monkeypatch.setattr("Urban_Amenities2.cli.main.aggregate_scores", boom)

    result = cli_runner.invoke(
        app,
        ["aggregate", str(subscores), "--weights", str(weights)],
    )

    assert result.exit_code == 1
    assert "Operation cancelled" in result.output


def test_aggregate_inline_weights_and_optional_outputs(
    cli_runner: CliRunner, tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    subscores = tmp_path / "subscores.csv"
    frame = pd.DataFrame(
        {
            "hex_id": ["abc"],
            "EA": [10.0],
            "LCA": [20.0],
            "contributors": [[{"metric": "EA", "weight": 0.5}]],
        }
    )
    frame.to_csv(subscores, index=False)

    output = tmp_path / "output.parquet"
    explain = tmp_path / "explain.parquet"
    report = tmp_path / "report.html"
    calls: dict[str, Any] = {}

    def fake_aggregate_scores(source: pd.DataFrame, value_column: str, weight_config: object) -> pd.DataFrame:
        calls["weights"] = getattr(weight_config, "weights", {})
        return source.assign(**{value_column: source["EA"] * 0.6 + source["LCA"] * 0.4})

    def fake_write_scores(df: pd.DataFrame, path: Path) -> None:
        calls["write_scores"] = path
        path.write_text("scores", encoding="utf-8")

    def fake_top_contributors(df: pd.DataFrame) -> pd.DataFrame:
        calls["explain_source"] = list(df["contributors"][0])
        return pd.DataFrame({"hex_id": ["abc"], "metric": ["EA"]})

    def fake_write_explainability(df: pd.DataFrame, path: Path) -> None:
        calls["write_explainability"] = path
        path.write_text("explain", encoding="utf-8")

    def fake_summary_statistics(df: pd.DataFrame, score_column: str) -> dict[str, float]:
        payload = {"mean": float(df[score_column].mean())}
        calls["summary"] = {"column": score_column, "payload": payload}
        return payload

    def fake_build_report(df: pd.DataFrame, original: pd.DataFrame, path: Path) -> None:
        calls["report_path"] = path
        path.write_text("report", encoding="utf-8")

    monkeypatch.setattr("Urban_Amenities2.cli.main.aggregate_scores", fake_aggregate_scores)
    monkeypatch.setattr("Urban_Amenities2.cli.main.write_scores", fake_write_scores)
    monkeypatch.setattr("Urban_Amenities2.cli.main.top_contributors", fake_top_contributors)
    monkeypatch.setattr("Urban_Amenities2.cli.main.write_explainability", fake_write_explainability)
    monkeypatch.setattr("Urban_Amenities2.cli.main.summary_statistics", fake_summary_statistics)
    monkeypatch.setattr("Urban_Amenities2.cli.main.build_report", fake_build_report)

    result = cli_runner.invoke(
        app,
        [
            "aggregate",
            str(subscores),
            "--weights",
            json.dumps({"EA": 0.6, "LCA": 0.4}),
            "--output",
            str(output),
            "--explainability-output",
            str(explain),
            "--report-path",
            str(report),
            "--run-id",
            "demo",
        ],
    )

    assert result.exit_code == 0
    assert "Wrote AUCS scores" in result.stdout
    assert "Wrote explainability" in result.stdout
    assert "QA report" in result.stdout
    assert calls["weights"] == {"EA": 0.6, "LCA": 0.4}
    assert calls["write_scores"] == output
    assert calls["write_explainability"] == explain
    assert calls["report_path"] == report
    assert calls["summary"]["column"] == "aucs"
    assert calls["summary"]["payload"]["mean"] == pytest.approx(14.0)
