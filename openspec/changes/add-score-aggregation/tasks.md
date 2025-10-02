## 1. Normalization (E38-E39)

- [x] 1.1 Implement metro-relative percentile normalization in `src/Urban_Amenities2/scores/normalization.py`
- [x] 1.2 Compute P5 and P95 per metro/state for each subscore
- [x] 1.3 Clamp to [P5, P95] and scale to [0, 100]
- [x] 1.4 Implement standards-based anchor normalization (E39)
- [x] 1.5 Allow configuration of normalization mode per subscore
- [x] 1.6 Write tests

## 2. Weighted Aggregation (E37)

- [x] 2.1 Implement AUCS aggregation in `src/Urban_Amenities2/scores/aggregation.py`
- [x] 2.2 Validate weights sum to 100
- [x] 2.3 Compute AUCS = Σ w_k · S_k for normalized subscores
- [x] 2.4 Write tests

## 3. Explainability

- [x] 3.1 Implement explainability in `src/Urban_Amenities2/scores/explainability.py`
- [x] 3.2 For each hex, extract top 5 contributing POIs per subscore
- [x] 3.3 Extract best modes and time slices
- [x] 3.4 For CTE, extract top corridor errand chains
- [x] 3.5 Store as JSON in explainability.parquet
- [x] 3.6 Write tests

## 4. Output Files

- [x] 4.1 Write final AUCS Parquet in `src/Urban_Amenities2/export/parquet.py`
- [x] 4.2 Include: hex_id, AUCS, all 7 subscores, run_id, timestamp
- [x] 4.3 Write explainability.parquet with contributors
- [x] 4.4 Generate summary statistics JSON
- [x] 4.5 Validate output schemas
- [x] 4.6 Write tests

## 5. QA Reporting and Visualization

- [x] 5.1 Create QA report generator in `src/Urban_Amenities2/export/reports.py`
- [x] 5.2 Generate distribution plots for AUCS and subscores
- [x] 5.3 Generate correlation matrix across subscores
- [x] 5.4 Create hex choropleths with folium or pydeck
- [x] 5.5 Output HTML report: `output/qa_report.html`
- [x] 5.6 Write tests

## 6. CLI Integration

- [x] 6.1 Add `aucs aggregate --run-id <id>` command
- [x] 6.2 Add `aucs show --hex <hex_id>` to display scores and contributors
- [x] 6.3 Add `aucs export --format geojson` for GIS tools
- [x] 6.4 Write tests
