# Mobility Options, Reliability & Resilience Implementation Tasks

## 1. Component 1: Frequent Transit Exposure (8 tasks)

- [ ] 1.1 Load GTFS static data (routes, trips, stop_times)
- [ ] 1.2 Compute headways for each stop and route
- [ ] 1.3 Identify stops with <15 min peak headway
- [x] 1.4 Compute % of transit stops within 500m of hex with frequent service
- [x] 1.5 Normalize to 0-100 scale (C₁)
- [ ] 1.6 Handle hexes with no nearby transit (C₁=0)
- [ ] 1.7 Test with dense transit areas (downtown) vs sparse (suburban)
- [ ] 1.8 Document C₁ computation

## 2. Component 2: Service Span (6 tasks)

- [ ] 2.1 Compute service hours per day for each nearby stop
- [ ] 2.2 Identify stops with early AM, late PM, and weekend service
- [x] 2.3 Compute weighted service span score (24h=100, 12h=50, 6h=25)
- [x] 2.4 Normalize to C₂ (0-100)
- [ ] 2.5 Test with 24h service vs limited service
- [ ] 2.6 Document C₂ computation

## 3. Component 3: On-Time Reliability (8 tasks)

- [ ] 3.1 Load GTFS-RT trip updates for reliability analysis
- [ ] 3.2 Compute mean delay per route (from trip update feed)
- [ ] 3.3 Compute on-time percentage (within ±5 min)
- [x] 3.4 Weight routes by frequency (more frequent = more weight)
- [ ] 3.5 Aggregate to hex level (all nearby routes)
- [x] 3.6 Normalize to C₃ (0-100, 100=100% on-time)
- [ ] 3.7 Handle missing GTFS-RT (use scheduled reliability proxy)
- [ ] 3.8 Document C₃ computation and data requirements

## 4. Component 4: Network Redundancy (8 tasks)

- [ ] 4.1 Count number of unique transit routes within 800m
- [ ] 4.2 Count number of road route alternatives (using OSRM)
- [x] 4.3 Compute redundancy score: R = 1 - 1/(1+routes)
- [x] 4.4 Normalize to C₄ (0-100)
- [ ] 4.5 Test with grid networks (high redundancy) vs linear (low)
- [ ] 4.6 Validate C₄ correlates with resilience
- [x] 4.7 Handle isolated areas (C₄=0)
- [ ] 4.8 Document C₄ computation

## 5. Component 5: Micromobility Presence (7 tasks)

- [ ] 5.1 Load GBFS (General Bikeshare Feed Specification) data for bike/scooter systems
- [ ] 5.2 Identify GBFS-enabled systems in CO/UT/ID
- [x] 5.3 Compute density of bikeshare/scooter stations within 500m
- [x] 5.4 Normalize to C₅ (0-100, 100=high density)
- [x] 5.5 Handle areas without micromobility (C₅=0)
- [ ] 5.6 Test with systems in Denver, SLC, Boise
- [ ] 5.7 Document C₅ computation and data sources

## 6. MORR Aggregation and Testing (8 tasks)

- [x] 6.1 Combine components: MORR = w₁·C₁ + w₂·C₂ + w₃·C₃ + w₄·C₄ + w₅·C₅
- [ ] 6.2 Load component weights from params.yaml (default equal weights)
- [x] 6.3 Normalize final MORR to 0-100 scale
- [ ] 6.4 Validate MORR score distributions
- [ ] 6.5 Integration test on pilot region
- [ ] 6.6 Compare MORR with known transit-rich vs transit-poor areas
- [ ] 6.7 Add MORR to total AUCS computation (12% weight)
- [ ] 6.8 Generate MORR choropleth for QA
