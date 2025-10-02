## 1. Normalization (E38-E39)

- [ ] 1.1 Implement metro-relative percentile normalization in `src/Urban_Amenities2/scores/normalization.py`
- [ ] 1.2 Compute P5 and P95 per metro/state for each subscore
- [ ] 1.3 Clamp to [P5, P95] and scale to [0, 100]
- [ ] 1.4 Implement standards-based anchor normalization (E39)
- [ ] 1.5 Allow configuration of normalization mode per subscore
- [ ] 1.6 Write tests

## 2. Weighted Aggregation (E37)

- [ ] 2.1 Implement AUCS aggregation in `src/Urban_Amenities2/scores/aggregation.py`
- [ ] 2.2 Validate weights sum to 100
- [ ] 2.3 Compute AUCS = Σ w_k · S_k for normalized subscores
- [ ] 2.4 Write tests

## 3. Explainability

- [ ] 3.1 Implement explainability in `src/Urban_Amenities2/scores/explainability.py`
- [ ] 3.2 For each hex, extract top 5 contributing POIs per subscore
- [ ] 3.3 Extract best modes and time slices
- [ ] 3.4 For CTE, extract top corridor errand chains
- [ ] 3.5 Store as JSON in explainability.parquet
- [ ] 3.6 Write tests

## 4. Output Files

- [ ] 4.1 Write final AUCS Parquet in `src/Urban_Amenities2/export/parquet.py`
- [ ] 4.2 Include: hex_id, AUCS, all 7 subscores, run_id, timestamp
- [ ] 4.3 Write explainability.parquet with contributors
- [ ] 4.4 Generate summary statistics JSON
- [ ] 4.5 Validate output schemas
- [ ] 4.6 Write tests

## 5. QA Reporting and Visualization

- [ ] 5.1 Create QA report generator in `src/Urban_Amenities2/export/reports.py`
- [ ] 5.2 Generate distribution plots for AUCS and subscores
- [ ] 5.3 Generate correlation matrix across subscores
- [ ] 5.4 Create hex choropleths with folium or pydeck
- [ ] 5.5 Output HTML report: `output/qa_report.html`
- [ ] 5.6 Write tests

## 6. CLI Integration

- [ ] 6.1 Add `aucs aggregate --run-id <id>` command
- [ ] 6.2 Add `aucs show --hex <hex_id>` to display scores and contributors
- [ ] 6.3 Add `aucs export --format geojson` for GIS tools
- [ ] 6.4 Write tests
