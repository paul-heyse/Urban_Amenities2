## Why
The UI data context now selects the newest `.parquet` file even when it is `metadata.parquet`, causing KeyErrors for missing score columns during Dash layout setup. Additionally, the `SliderTooltip` type alias was dropped from `ui.types`, breaking typed imports for filter components.

## What Changes
- Scope DataContext refresh to score datasets (e.g., files ending in `_scores.parquet`) before joining metadata, eliminating false positives from support files.
- Restore a typed `SliderTooltip` helper so filter and parameter panels can configure dash sliders without import errors.
- Add regression tests covering dataset detection and the filter/parameter panel construction.

## Impact
- Affected specs: ui-data, ui-components
- Affected code: `src/Urban_Amenities2/ui/data_loader.py`, `src/Urban_Amenities2/ui/types.py`, UI component tests
