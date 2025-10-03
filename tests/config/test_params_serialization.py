from __future__ import annotations

from pathlib import Path

from Urban_Amenities2.config.loader import load_params
from Urban_Amenities2.config.params import AUCSParams


def test_params_round_trip_json(minimal_config_file: Path) -> None:
    params, _ = load_params(minimal_config_file)
    payload = params.model_dump_json(by_alias=True)
    restored = AUCSParams.model_validate_json(payload)
    assert restored == params


def test_optional_defaults_present(minimal_config_file: Path) -> None:
    params, _ = load_params(minimal_config_file)
    assert params.compute.preload_hex_neighbors is True
    assert params.leisure_cross_category.novelty.max_bonus == 0.2
