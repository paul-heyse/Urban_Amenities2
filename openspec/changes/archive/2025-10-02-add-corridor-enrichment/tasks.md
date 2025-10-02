# Corridor Trip-Chaining Enrichment Implementation Tasks

## 1. Transit Path Identification (10 tasks)

- [x] 1.1 Query OTP2 for top 2 transit paths from hex to CBD/major hub
- [x] 1.2 Define major hubs per metro (downtown Denver, SLC, Boise)
- [x] 1.3 Extract stop sequences from each path
- [x] 1.4 Filter paths with <5 stops (too short for errand chains)
- [x] 1.5 Rank paths by frequency and directness
- [x] 1.6 Cache path computations (reuse across hexes)
- [x] 1.7 Handle hexes with no transit paths (CTE=0)
- [x] 1.8 Test path identification for sample hexes
- [x] 1.9 Validate path coverage (% hexes with ≥1 path)
- [x] 1.10 Document path identification logic

## 2. Stop Buffering and POI Collection (8 tasks)

- [x] 2.1 Buffer each stop by 350m walking distance
- [x] 2.2 Query POIs within each stop buffer
- [x] 2.3 Filter to errand-friendly categories (grocery, pharmacy, bank, post, childcare)
- [x] 2.4 Deduplicate POIs appearing in multiple buffers
- [x] 2.5 Store POI-to-stop mapping
- [x] 2.6 Test with dense stops (downtown) vs sparse (suburban)
- [x] 2.7 Optimize spatial queries (use rtree index)
- [x] 2.8 Document buffering and POI collection

## 3. Errand Chain Scoring (10 tasks)

- [x] 3.1 Define common 2-stop chains (grocery+pharmacy, bank+post, grocery+childcare)
- [x] 3.2 Identify feasible chains (both amenities present in different stop buffers)
- [x] 3.3 Compute detour time for each chain (compared to direct trip)
- [x] 3.4 Filter chains with detour >10 min (too inconvenient)
- [x] 3.5 Score chains by quality (Q_a of both amenities)
- [x] 3.6 Weight chains by likelihood (frequent vs rare combinations)
- [x] 3.7 Aggregate chains to corridor-level score
- [x] 3.8 Normalize to CTE subscore (0-100)
- [x] 3.9 Test with known trip-chaining corridors
- [x] 3.10 Validate CTE correlates with transit-oriented development

## 4. Integration and Testing (7 tasks)

- [x] 4.1 Integrate CTE into total AUCS computation (5% weight)
- [x] 4.2 Run CTE computation on pilot region
- [x] 4.3 Validate CTE distributions (expect higher scores near transit)
- [x] 4.4 Compare CTE with/without detour constraint
- [x] 4.5 Generate CTE choropleth map for QA
- [x] 4.6 Property test: CTE in [0, 100]
- [x] 4.7 Document CTE methodology and parameters
