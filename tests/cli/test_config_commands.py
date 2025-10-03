from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from Urban_Amenities2.cli.main import app


def test_config_validate_success(cli_runner: CliRunner, minimal_config_file: Path) -> None:
    result = cli_runner.invoke(app, ["config", "validate", str(minimal_config_file)])
    assert result.exit_code == 0
    assert "is valid" in result.stdout


def test_config_validate_failure(cli_runner: CliRunner, invalid_type_config_file: Path) -> None:
    result = cli_runner.invoke(app, ["config", "validate", str(invalid_type_config_file)])
    assert result.exit_code == 1
    assert "Error:" in result.stdout


def test_config_show_outputs_summary(cli_runner: CliRunner, minimal_config_file: Path) -> None:
    result = cli_runner.invoke(app, ["config", "show", str(minimal_config_file)])
    assert result.exit_code == 0
    assert "AUCS Parameters" in result.stdout
    assert "Subscore Weights" in result.stdout


def test_config_show_handles_error(cli_runner: CliRunner, tmp_path: Path) -> None:
    missing = tmp_path / "missing.yml"
    result = cli_runner.invoke(app, ["config", "show", str(missing)])
    assert result.exit_code == 1
    assert "Error:" in result.stdout
