from __future__ import annotations

from pathlib import Path
from typing import Iterator

import pytest
from ruamel.yaml import YAML

def _copy_fixture(tmp_path: Path, fixture: Path) -> Path:
    target = tmp_path / fixture.name
    target.write_text(fixture.read_text(), encoding="utf-8")
    return target


@pytest.fixture(scope="session")
def config_fixtures_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "configs"


@pytest.fixture()
def minimal_config_file(tmp_path: Path, config_fixtures_dir: Path) -> Path:
    return _copy_fixture(tmp_path, config_fixtures_dir / "minimal.yml")


@pytest.fixture()
def invalid_type_config_file(tmp_path: Path, config_fixtures_dir: Path) -> Path:
    return _copy_fixture(tmp_path, config_fixtures_dir / "invalid_type.yml")


@pytest.fixture()
def yaml_loader() -> Iterator[YAML]:
    loader = YAML(typ="safe")
    yield loader
