# Essentials Access (EA) Subscore

The Essentials Access subscore quantifies how well a hexagon is served by key
amenities such as groceries, healthcare, childcare, and daily needs. It aligns
with the equations defined in the OpenSpec change `add-essentials-access`.

## Components

1. **Quality-weighted accessibility** – For each POI `a` serving hex `i`, we
   compute `z_{i,a} = (Q_a · w_{i,a})^{\rho_c}` where `Q_a` reflects intrinsic
   quality (brand, enrichment) and `w_{i,a}` is the accessibility weight derived
   from travel-time matrices. Elasticity `\rho_c` is configured per category.
2. **CES aggregation** – Category exposure is `V_{i,c} = (\sum_a z_{i,a})^{1/\rho_c}`
   implemented in `math.ces.ces_aggregate`. Edge cases such as empty categories or
   zero weights return zero.
3. **Satiation** – Category scores are `S_{i,c} = 100 · (1 - exp(-\kappa_c · V_{i,c}))`
   using `math.satiation.apply_satiation`. `\kappa_c` may be fixed or computed
   from anchors (`compute_kappa_from_anchor`).
4. **Diversity bonus** – `math.diversity.compute_diversity` applies Shannon
   entropy by subtype (brand, category) and converts the result into a capped bonus
   using `DiversityConfig` weights.
5. **Shortfall penalty** – `scores.penalties.shortfall_penalty` deducts points
   when categories fall below a threshold (default 20). Penalties accumulate up to
   a configurable cap.
6. **Explainability** – `EssentialsAccessCalculator` records the top contributors
   per category (`scores.explainability.top_contributors`) for transparency.

## Workflow

`EssentialsAccessCalculator.compute(pois, accessibility)` returns two DataFrames:

* `ea_scores` – columns `hex_id`, `EA`, `penalty`, `category_scores`,
  `contributors`. Validated by `schemas.scores.EAOutputSchema` and persisted via
  CLI or export helpers.
* `category_scores` – per-hex, per-category breakdown with satiation, diversity
  bonus, entropy, and raw `V` values.

## Configuration

`EssentialsAccessConfig` bundles:

* `categories` – ordered list of AUCS essential types (e.g. groceries, health,
  childcare).
* `category_params` – mapping from category to `EssentialCategoryConfig` (rho,
  kappa, diversity weights).
* `shortfall_threshold`, `shortfall_penalty`, `shortfall_cap` – control penalty
  logic.
* `top_k`, `batch_size` – tune explainability depth and memory usage.

Adjust parameters by editing your YAML configuration or by running the CLI
calibration command:

```bash
aucs calibrate ea pois.parquet accessibility.parquet --parameter rho:groceries --values 0.4,0.6,0.8
```

## Outputs and Exports

* The CLI command `aucs score ea` writes aggregated scores to Parquet and
  optionally category-level outputs.
* `export.parquet.write_scores` and `export.parquet.write_explainability`
  persist EA results alongside contributors for dashboards.
* `export.reports.build_report` can incorporate EA as part of the broader AUCS QA
  report.

See `tests/test_scores.py` and `tests/test_cli.py` for executable examples.
