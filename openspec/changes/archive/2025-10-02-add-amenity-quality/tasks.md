# Amenity Quality Implementation Tasks

## 1. Quality Scoring Framework (15 tasks)

- [x] 1.1 Create `src/Urban_Amenities2/quality/scoring.py` module
- [x] 1.2 Implement size/capacity scoring (square footage, seating, collection size from Overture/Wikidata)
- [x] 1.3 Implement popularity scoring (Wikipedia pageviews, Wikidata sitelink count)
- [x] 1.4 Implement brand recognition scoring (chain status, Wikidata brand property)
- [x] 1.5 Implement heritage flags (historic designation, museum/library status)
- [x] 1.6 Normalize scores to 0-100 scale per component
- [x] 1.7 Combine components with weighted sum for total Q_a
- [x] 1.8 Implement opening hours bonus (24/7 > extended > limited > seasonal)
- [x] 1.9 Handle missing data (use category defaults)
- [x] 1.10 Validate Q_a ranges (0-100, no NaN)
- [x] 1.11 Compute Q_a for all POIs in dataset
- [x] 1.12 Store Q_a in POI Parquet file (add column)
- [x] 1.13 Create Q_a summary statistics per category
- [x] 1.14 Add Q_a to hex detail explainability output
- [x] 1.15 Document Q_a calculation methodology

## 2. Brand Deduplication (10 tasks)

- [x] 2.1 Create `src/Urban_Amenities2/quality/dedupe.py` module
- [x] 2.2 Identify brand chains (use Wikidata brand property or name matching)
- [x] 2.3 Implement proximity penalty for same-brand POIs (E8)
- [x] 2.4 Compute pairwise distances between same-brand POIs
- [x] 2.5 Apply distance-based weight reduction (closer = lower weight)
- [x] 2.6 Set deduplication threshold (e.g., <500m for same brand)
- [x] 2.7 Test deduplication with dense areas (many chains)
- [x] 2.8 Validate total weight preserved across dedupe
- [x] 2.9 Log deduplication statistics (% POIs affected)
- [x] 2.10 Document brand deduplication parameters

## 3. Testing and Validation (10 tasks)

- [x] 3.1 Unit test Q_a scoring components (size, popularity, brand, heritage)
- [x] 3.2 Test with synthetic POI data (known attributes)
- [x] 3.3 Property-based test: Q_a in [0, 100]
- [x] 3.4 Test opening hours bonus logic (all hour patterns)
- [x] 3.5 Test brand deduplication (verify weight reduction)
- [x] 3.6 Integration test with real Overture + Wikidata data
- [x] 3.7 Spot-check Q_a values for known POIs (flagship stores, heritage sites)
- [x] 3.8 Compare Q_a distributions across categories
- [x] 3.9 Validate Q_a impact on accessibility scores (higher Q_a → higher scores)
- [x] 3.10 Document test coverage and validation results
