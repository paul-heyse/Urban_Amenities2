from __future__ import annotations

import pytest
from typer import Typer
from typer.testing import CliRunner

from Urban_Amenities2.cli.main import app


@pytest.fixture()
def cli_runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def cli_app() -> Typer:
    return app
