from __future__ import annotations

from typer.testing import CliRunner

from Urban_Amenities2.cli.main import app


def test_cli_main_help_lists_key_commands(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    stdout = result.stdout
    for command in ["config", "ingest", "score", "aggregate", "export"]:
        assert command in stdout


def test_cli_score_help_lists_subcommands(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(app, ["score", "--help"])

    assert result.exit_code == 0
    stdout = result.stdout
    assert "Scoring commands" in stdout
    assert "ea" in stdout
