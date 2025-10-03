from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
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


def test_aggregate_command_handles_missing_file(
    cli_runner: CliRunner, tmp_path: Path
) -> None:
    weights = tmp_path / "weights.json"
    _write_weights(weights)
    missing = tmp_path / "missing.csv"
    result = cli_runner.invoke(
        app, ["aggregate", str(missing), "--weights", str(weights)]
    )
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
