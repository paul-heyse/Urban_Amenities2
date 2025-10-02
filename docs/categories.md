# Category Crosswalk

The AUCS taxonomy groups Overture Places categories into a curated set of
"aucstype" values that power Essentials Access scoring and broader aggregation.
The mapping lives in `docs/AUCS place category crosswalk` as a YAML file with
three primary blocks:

* `include` – lists category prefixes that should map to a given AUCS type.
* `exclude` – removes specific sub-categories even if the prefix matches the
  inclusion rule.
* `overrides` – explicit POI IDs or brands that receive a fixed AUCS label.

`xwalk.overture_aucs.CategoryMatcher` loads this document and exposes a
`matcher.assign(frame)` helper used by `io.overture.places.PlacesPipeline`. The
matcher evaluates `primary_category` first, then falls back to
`alternate_categories`.

## Adding or Updating Categories

1. Edit the YAML document, preserving the prefix-based structure.
2. Keep category names snake_cased (e.g. `groceries_superstore`).
3. Run the unit tests (`pytest -q`) to ensure the matcher still assigns expected
   outputs (`tests/test_data_ingestion.py::test_crosswalk_and_dedupe`).
4. Update `docs/subscores/essentials_access.md` if new essential categories are
   introduced so scoring documentation stays aligned.

## Example Structure

```yaml
include:
  groceries_superstore:
    - shop.grocery.supermarket
    - shop.department.big_box
exclude:
  groceries_superstore:
    - shop.department.big_box.vehicle_only
overrides:
  poi:12345: groceries_speciality
```

The matcher lowercases categories, trims whitespace, and supports nested
prefixes such as `eat_and_drink.restaurant`. Brands can be used as a final
fallback when category metadata is ambiguous.
