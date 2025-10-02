from __future__ import annotations

from Urban_Amenities2 import load_params


def test_package_exposes_loader() -> None:
    params, param_hash = load_params("configs/params_default.yml")
    assert params.grid.hex_size_m == 250
    assert len(param_hash) == 64
