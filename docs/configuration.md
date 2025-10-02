# Parameter Configuration Reference

The AUCS parameter loader expects a YAML document that mirrors the
`Urban_Amenities2.config.params.AUCSParams` model. Key sections include:

- **grid** – spatial resolution and search limits. `hex_size_m` controls the
  H3 edge length while `isochrone_minutes` defines travel time rings.
- **subscores** – weights for the AUCS subscores. They must sum to 100.
- **time_slices** – time-of-day slices with relative weights and value of time
  (VOT) figures.
- **modes / nests / logit** – definitions required for the nested logit model,
  including per-mode coefficients, decay half-life, and nest membership.
- **carry_penalty / quality** – parameters for goods carrying penalties and POI
  quality calculations.
- **categories / leisure_cross_category** – category groupings, satiation
  behaviour, and cross-category blending weights. Anchor satiation targets are
  converted into kappa values automatically. `ces_rho` may be provided as a
  per-category mapping and diversity settings expose `weight`,
  `min_multiplier`, and `max_multiplier` for the Shannon-based bonus.
- **hubs_airports / jobs_education / morr / corridor / seasonality** –
  supporting subsystems for accessibility, resilience, and comfort.
- **corridor** – trip-chaining settings including `major_hubs` per metro,
  allowed `pair_categories`, decay parameters, and cache sizing for OTP path
  lookups. Chain likelihoods can be tuned via `chain_weights`.
- **normalization / compute** – percentile targets and compute-time behaviour
  such as caching and top-K selection.

Use `configs/params_default.yml` as a starting point. Validate files via:

```bash
python -m Urban_Amenities2.cli.main config-validate configs/params_default.yml
```

Display a formatted summary:

```bash
python -m Urban_Amenities2.cli.main config-show configs/params_default.yml
```

The loader computes a deterministic hash for reproducibility; downstream run
manifests store this alongside data snapshot IDs.
