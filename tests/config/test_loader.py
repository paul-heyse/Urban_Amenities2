from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping

import pytest
from ruamel.yaml import YAML

from Urban_Amenities2.config.loader import ParameterLoadError, compute_param_hash, load_params
from Urban_Amenities2.config.params import AUCSParams


def test_load_params_success(minimal_config_file: Path) -> None:
    params, param_hash = load_params(minimal_config_file)
    assert isinstance(params, AUCSParams)
    assert params.grid.hex_size_m == 250
    assert param_hash == compute_param_hash(params)


def test_load_params_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "missing.yml"
    with pytest.raises(ParameterLoadError) as excinfo:
        load_params(missing)
    assert "does not exist" in str(excinfo.value)


def test_load_params_malformed_yaml(tmp_path: Path) -> None:
    malformed = tmp_path / "malformed.yml"
    malformed.write_text("grid: [unbalanced", encoding="utf-8")
    with pytest.raises(ParameterLoadError) as excinfo:
        load_params(malformed)
    assert "Failed to parse" in str(excinfo.value)


def test_load_params_missing_section(minimal_config_file: Path, tmp_path: Path, yaml_loader: YAML) -> None:
    data = yaml_loader.load(minimal_config_file.read_text())
    data.pop("grid")
    missing = tmp_path / "missing.yml"
    with missing.open("w", encoding="utf-8") as handle:
        yaml_loader.dump(data, handle)
    with pytest.raises(ParameterLoadError) as excinfo:
        load_params(missing)
    assert "grid" in str(excinfo.value)


def test_load_params_with_override(minimal_config_file: Path, tmp_path: Path, yaml_loader: YAML) -> None:
    override_data = {"grid": {"hex_size_m": 320}}
    override_path = tmp_path / "override.yml"
    with override_path.open("w", encoding="utf-8") as handle:
        yaml_loader.dump(override_data, handle)
    params, _ = load_params(minimal_config_file, override=override_path)
    assert params.grid.hex_size_m == 320


def test_load_params_env_override(minimal_config_file: Path) -> None:
    env = {"AUCS_grid__hex_size_m": "375"}
    params, _ = load_params(minimal_config_file, env=env)
    assert params.grid.hex_size_m == 375


def test_load_params_precedence(minimal_config_file: Path, tmp_path: Path, yaml_loader: YAML) -> None:
    override_data = {"grid": {"hex_size_m": 260}}
    override_path = tmp_path / "override.yml"
    with override_path.open("w", encoding="utf-8") as handle:
        yaml_loader.dump(override_data, handle)
    env = {"AUCS_grid__hex_size_m": "410"}
    params, _ = load_params(minimal_config_file, override=override_path, env=env)
    assert params.grid.hex_size_m == 410


def test_load_params_invalid_type(invalid_type_config_file: Path) -> None:
    with pytest.raises(ParameterLoadError) as excinfo:
        load_params(invalid_type_config_file)
    message = str(excinfo.value)
    assert "hex_size_m" in message
    assert "number" in message.lower()


def test_param_hash_changes_with_override(minimal_config_file: Path, tmp_path: Path, yaml_loader: YAML) -> None:
    params, original_hash = load_params(minimal_config_file)
    override_data = {"grid": {"hex_size_m": params.grid.hex_size_m + 10}}
    override_path = tmp_path / "override.yml"
    with override_path.open("w", encoding="utf-8") as handle:
        yaml_loader.dump(override_data, handle)
    merged, _ = load_params(minimal_config_file, override=override_path)
    assert compute_param_hash(merged) != original_hash
