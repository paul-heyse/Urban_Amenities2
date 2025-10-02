# Amenity Quality Implementation Tasks

## 1. Quality Scoring Framework (15 tasks)

- [ ] 1.1 Create `src/Urban_Amenities2/quality/scoring.py` module
- [ ] 1.2 Implement size/capacity scoring (square footage, seating, collection size from Overture/Wikidata)
- [ ] 1.3 Implement popularity scoring (Wikipedia pageviews, Wikidata sitelink count)
- [ ] 1.4 Implement brand recognition scoring (chain status, Wikidata brand property)
- [ ] 1.5 Implement heritage flags (historic designation, museum/library status)
- [ ] 1.6 Normalize scores to 0-100 scale per component
- [ ] 1.7 Combine components with weighted sum for total Q_a
- [ ] 1.8 Implement opening hours bonus (24/7 > extended > limited > seasonal)
- [ ] 1.9 Handle missing data (use category defaults)
- [ ] 1.10 Validate Q_a ranges (0-100, no NaN)
- [ ] 1.11 Compute Q_a for all POIs in dataset
- [ ] 1.12 Store Q_a in POI Parquet file (add column)
- [ ] 1.13 Create Q_a summary statistics per category
- [ ] 1.14 Add Q_a to hex detail explainability output
- [ ] 1.15 Document Q_a calculation methodology

## 2. Brand Deduplication (10 tasks)

- [ ] 2.1 Create `src/Urban_Amenities2/quality/dedupe.py` module
- [ ] 2.2 Identify brand chains (use Wikidata brand property or name matching)
- [ ] 2.3 Implement proximity penalty for same-brand POIs (E8)
- [ ] 2.4 Compute pairwise distances between same-brand POIs
- [ ] 2.5 Apply distance-based weight reduction (closer = lower weight)
- [ ] 2.6 Set deduplication threshold (e.g., <500m for same brand)
- [ ] 2.7 Test deduplication with dense areas (many chains)
- [ ] 2.8 Validate total weight preserved across dedupe
- [ ] 2.9 Log deduplication statistics (% POIs affected)
- [ ] 2.10 Document brand deduplication parameters

## 3. Testing and Validation (10 tasks)

- [ ] 3.1 Unit test Q_a scoring components (size, popularity, brand, heritage)
- [ ] 3.2 Test with synthetic POI data (known attributes)
- [ ] 3.3 Property-based test: Q_a in [0, 100]
- [ ] 3.4 Test opening hours bonus logic (all hour patterns)
- [ ] 3.5 Test brand deduplication (verify weight reduction)
- [ ] 3.6 Integration test with real Overture + Wikidata data
- [ ] 3.7 Spot-check Q_a values for known POIs (flagship stores, heritage sites)
- [ ] 3.8 Compare Q_a distributions across categories
- [ ] 3.9 Validate Q_a impact on accessibility scores (higher Q_a → higher scores)
- [ ] 3.10 Document test coverage and validation results
