# Score Normalization and Final AUCS Aggregation

## Why

After computing all subscores (EA, LCA, MUHAA, JEA, MORR, CTE, SOU), we must:

1. **Normalize** each subscore to 0-100 scale using metro-relative percentiles or absolute anchors (E38-E39)
2. **Aggregate** subscores into final AUCS using weighted sum with configured weights (E37)
3. Generate **explainability artifacts** showing top contributors per hex

This change completes the scoring pipeline and produces the final outputs for visualization and analysis.

## What Changes

- Implement metro-relative percentile normalization (E38) with P5-P95 clamping
- Implement standards-based anchor normalization (E39) for cross-metro comparability
- Implement weighted aggregation (E37) with validation that weights sum to 100
- Generate per-hex explainability: top amenities, best modes, corridor baskets
- Write final output Parquet files with all subscores + AUCS + metadata
- Create summary statistics and distribution reports
- Generate QA visualizations (hex choropleths, subscore correlations)
- Add CLI commands for scoring runs and output inspection
- **BREAKING**: Establishes final AUCS output schema and file formats

## Impact

- Affected specs: `normalization`, `final-aucs`, `explainability` (all new)
- Affected code: Creates `src/Urban_Amenities2/` modules:
  - `scores/normalization.py` - Percentile and anchor normalization (E38-E39)
  - `scores/aggregation.py` - Weighted AUCS sum (E37)
  - `scores/explainability.py` - Top contributors, attribution
  - `export/parquet.py` - Final output writers
  - `export/reports.py` - Summary statistics and QA reports
  - `viz/maps.py` - Hex choropleths using folium/pydeck
- Dependencies: Adds altair, folium or pydeck
- Outputs final files:
  - `output/aucs.parquet` - hex_id, AUCS, all subscores, run_id
  - `output/explainability.parquet` - hex_id, top_contributors JSON
  - `output/summary_stats.json` - Distribution statistics
  - `output/qa_report.html` - Quality assurance visualizations
