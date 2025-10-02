from __future__ import annotations

from pathlib import Path

import pytest

from Urban_Amenities2.config.loader import ParameterLoadError, compute_param_hash, load_params
from Urban_Amenities2.config.params import AUCSParams


def test_load_default_params(tmp_path: Path) -> None:
    params_path = Path("configs/params_default.yml")
    params, param_hash = load_params(params_path)
    assert isinstance(params, AUCSParams)
    assert len(list(params.iter_time_slice_ids())) == 2
    derived = params.derived_satiation()
    assert "groceries" in derived
    assert param_hash == compute_param_hash(params)


def test_subscore_validation(tmp_path: Path, tmp_path_factory: pytest.TempPathFactory) -> None:
    invalid = tmp_path / "invalid.yml"
    invalid.write_text(
        """
        grid:
          hex_size_m: 250
          isochrone_minutes: [5]
          search_cap_minutes: 10
        subscores:
          EA: 10
          LCA: 10
          MUHAA: 10
          JEA: 10
          MORR: 10
          CTE: 10
          SOU: 10
        time_slices:
          - id: one
            weight: 1
            VOT_per_hour: 10
        modes:
          walk:
            name: walk
            theta_iv: -0.1
            theta_wait: -0.1
            theta_walk: -0.1
            transfer_penalty_min: 0
            half_life_min: 10
            beta0: 0
        nests:
          - id: base
            modes: [walk]
            mu: 1
            eta: 1
        logit:
          mu_top: 1
        carry_penalty:
          category_multipliers: {a: 1}
          per_mode_extra_minutes: {walk: 1}
        quality:
          lambda_weights: {rating: 1}
          z_clip_abs: 1
          opening_hours_bonus_xi: 1
          dedupe_beta_per_km: 1
        categories:
          essentials: [a]
          leisure: []
          ces_rho: 1
        leisure_cross_category:
          weights: {arts: 1}
          elasticity_zeta: 1
        hubs_airports:
          hub_mass_lambda: 1
          decay: 1
          airport_weights: {DEN: 1}
        jobs_education:
          university_weight_kappa: 1
          industry_weights: {tech: 1}
        morr:
          frequent_exposure: 1
          span: 1
          reliability: 1
          redundancy: 1
          micromobility: 1
        corridor:
          max_paths: 1
          stop_buffer_m: 1
          detour_cap_min: 1
          pair_categories: []
          walk_decay_alpha: 1
        seasonality:
          comfort_index_default: 1
        normalization:
          mode: metro
        compute:
          topK_per_category: 1
          hub_max_minutes: 1
        """
    )
    with pytest.raises(ParameterLoadError):
        load_params(invalid)


def test_param_hash_changes(tmp_path: Path) -> None:
    params_path = Path("configs/params_default.yml")
    params, param_hash = load_params(params_path)
    modified = params.model_copy()
    modified.compute.topK_per_category = params.compute.topK_per_category + 1
    assert compute_param_hash(modified) != param_hash
