from __future__ import annotations

from pathlib import Path

import pytest

from Urban_Amenities2.config.loader import load_params
from Urban_Amenities2.config.params import (
    AUCSParams,
    CategoryConfig,
    CategoryDiversityConfig,
    CorridorConfig,
    GridConfig,
    HubsAirportsConfig,
    LeisureCrossCategoryConfig,
    SubscoreWeights,
)


def test_grid_config_requires_sorted_isochrones() -> None:
    with pytest.raises(ValueError, match="sorted ascending"):
        GridConfig(hex_size_m=200, isochrone_minutes=[10, 5], search_cap_minutes=15)


def test_subscore_weights_must_total_100() -> None:
    with pytest.raises(ValueError, match="total 100"):
        SubscoreWeights(EA=20, LCA=20, MUHAA=20, JEA=10, MORR=10, CTE=10, SOU=5)


def test_category_config_direct_requires_positive_kappa() -> None:
    config = CategoryConfig(
        essentials=["groceries"],
        leisure=[],
        ces_rho=0.5,
        satiation_mode="direct",
        satiation_kappa=-0.1,
    )

    with pytest.raises(ValueError, match="positive"):
        config.derived_satiation()


def test_category_config_anchor_requires_targets() -> None:
    config = CategoryConfig(
        essentials=["groceries"],
        leisure=[],
        ces_rho={"groceries": 0.5},
        satiation_mode="anchor",
    )

    with pytest.raises(ValueError, match="requires satiation_targets"):
        config.derived_satiation()


def test_category_config_derived_helpers() -> None:
    diversity = {
        "essentials": CategoryDiversityConfig(weight=0.3, min_multiplier=1.0, max_multiplier=1.2)
    }
    config = CategoryConfig(
        essentials=["groceries"],
        leisure=["parks"],
        ces_rho={"groceries": 0.6, "parks": 0.4},
        satiation_mode="direct",
        satiation_kappa={"groceries": 0.5, "parks": 0.3},
        diversity=diversity,
    )

    satiation = config.derived_satiation()
    assert satiation["groceries"] == pytest.approx(0.5)
    assert satiation["parks"] == pytest.approx(0.3)
    rho = config.derived_rho()
    assert rho == {"groceries": pytest.approx(0.6), "parks": pytest.approx(0.4)}
    assert config.get_diversity("groceries") is diversity["essentials"]


def test_category_config_derived_rho_missing_category() -> None:
    config = CategoryConfig(
        essentials=["groceries"],
        leisure=[],
        ces_rho={"parks": 0.5},
    )

    with pytest.raises(ValueError, match="Missing CES rho"):
        config.derived_rho()


def test_leisure_cross_category_rejects_negative_weights() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        LeisureCrossCategoryConfig(weights={"arts": -0.5}, elasticity_zeta=1.0)


def test_hubs_airports_requires_positive_weights() -> None:
    with pytest.raises(ValueError, match="must contain positive"):
        HubsAirportsConfig(hub_mass_weights={"DEN": 0.0}, hub_decay_alpha=0.1, airport_decay_alpha=0.1)


def test_corridor_pair_categories_require_pairs() -> None:
    with pytest.raises(ValueError, match="exactly two"):
        CorridorConfig(
            max_paths=1,
            stop_buffer_m=10.0,
            detour_cap_min=5.0,
            pair_categories=[["a"]],
            walk_decay_alpha=0.1,
        )


def test_aucs_params_helpers(minimal_config_file: Path) -> None:
    params, _ = load_params(minimal_config_file)

    alphas = params.derived_mode_alphas()
    assert set(alphas) == {"walk"}
    mode_config = params.modes["walk"]
    assert alphas["walk"] == pytest.approx(mode_config.decay_alpha)

    assert params.derived_satiation() == {}
    assert list(params.iter_time_slice_ids()) == ["peak", "offpeak"]


def test_aucs_params_rejects_missing_modes(minimal_config_file: Path) -> None:
    params_data, _ = load_params(minimal_config_file)
    payload = params_data.model_dump(mode="python", by_alias=True)
    payload["nests"][0]["modes"] = ["nonexistent"]
    with pytest.raises(ValueError, match="undefined modes"):
        AUCSParams.model_validate(payload)
