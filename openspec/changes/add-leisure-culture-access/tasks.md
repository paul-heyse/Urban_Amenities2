# Leisure & Culture Access Implementation Tasks

## 1. LCA Core Implementation (15 tasks)

- [x] 1.1 Create `src/Urban_Amenities2/scores/leisure_culture_access.py` module
- [x] 1.2 Define 8 LCA categories: restaurants, cafes, bars, cinemas, performing_arts, museums_galleries, parks_trails, sports_rec
- [x] 1.3 Load POIs for each LCA category from processed data
- [x] 1.4 Compute accessibility weights w_ia for all LCA POIs (from travel time computation)
- [x] 1.5 Apply quality scores Q_a to LCA POIs
- [x] 1.6 Aggregate within each category using CES + satiation
- [x] 1.7 Compute cross-category CES aggregation (E17)
- [x] 1.8 Apply novelty bonus based on Wikipedia pageview volatility (E18)
- [x] 1.9 Normalize LCA subscore to 0-100 scale
- [x] 1.10 Handle edge cases (hexes with zero LCA amenities)
- [x] 1.11 Validate LCA score ranges and distributions
- [x] 1.12 Export LCA subscores to output Parquet
- [x] 1.13 Add LCA to total AUCS computation (18% weight)
- [x] 1.14 Generate LCA summary statistics per metro
- [x] 1.15 Document LCA methodology and parameters

## 2. Novelty Bonus (8 tasks)

- [x] 2.1 Load Wikipedia pageview time series for LCA POIs
- [x] 2.2 Compute pageview volatility (standard deviation of daily views)
- [x] 2.3 Normalize volatility to novelty score (0-20% bonus)
- [x] 2.4 Apply novelty bonus to Q_a before aggregation
- [x] 2.5 Test novelty with trending vs stable venues
- [x] 2.6 Handle POIs without pageview data (no bonus)
- [x] 2.7 Validate novelty bonus impact on LCA scores
- [x] 2.8 Document novelty calculation

## 3. Testing and Validation (7 tasks)

- [x] 3.1 Unit test LCA category aggregation
- [x] 3.2 Test cross-category CES (verify substitution across leisure types)
- [x] 3.3 Integration test on pilot region (Boulder, CO)
- [x] 3.4 Compare LCA scores with known leisure districts (high) vs suburbs (low)
- [x] 3.5 Validate LCA weight in total AUCS (18%)
- [x] 3.6 Property test: LCA in [0, 100]
- [x] 3.7 Generate LCA choropleth map for QA
