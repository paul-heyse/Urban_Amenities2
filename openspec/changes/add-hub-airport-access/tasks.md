# Major Urban Hub & Airport Access Implementation Tasks

## 1. Hub Mass Calculation (12 tasks)

- [x] 1.1 Load CBSA (Core-Based Statistical Area) boundaries
- [x] 1.2 Load population data per CBSA (Census)
- [x] 1.3 Load GDP data per CBSA (BEA Regional Economic Accounts)
- [x] 1.4 Count POIs per CBSA from Overture data
- [x] 1.5 Count cultural institutions per CBSA (museums, theaters, universities)
- [x] 1.6 Normalize each mass component to 0-100 scale
- [x] 1.7 Compute combined hub mass: M = w_pop·Pop + w_gdp·GDP + w_poi·POI + w_culture·Culture
- [x] 1.8 Load component weights from params.yaml
- [x] 1.9 Validate mass scores for known hubs (Denver > Pueblo)
- [x] 1.10 Store hub mass in reference table
- [x] 1.11 Test with all CBSAs in CO/UT/ID
- [x] 1.12 Document hub mass methodology

## 2. Hub Accessibility (10 tasks)

- [x] 2.1 Compute travel times from each hex to each CBSA centroid
- [x] 2.2 Use best mode (transit or car) per OD pair
- [x] 2.3 Compute generalized travel cost (GTC) for each hub
- [x] 2.4 Apply decay function: A_hub = Σ(M_hub · exp(-α · GTC_hub))
- [x] 2.5 Load decay parameter α from params.yaml
- [x] 2.6 Normalize hub accessibility to 0-100 scale
- [x] 2.7 Test with central vs peripheral hexes
- [x] 2.8 Validate hub accessibility correlates with regional connectivity
- [x] 2.9 Handle hexes with no reachable hubs (score=0)
- [x] 2.10 Document hub accessibility computation

## 3. Airport Accessibility (10 tasks)

- [x] 3.1 Load FAA airport enplanement data (annual passengers)
- [x] 3.2 Filter to airports in/near CO/UT/ID (DEN, SLC, BOI, COS, etc.)
- [x] 3.3 Compute travel times from each hex to each airport
- [x] 3.4 Use best mode (car typically; transit if available)
- [x] 3.5 Compute GTC for each airport
- [x] 3.6 Apply decay with enplanement weighting: A_airport = Σ(Enplane · exp(-α · GTC))
- [x] 3.7 Normalize airport accessibility to 0-100 scale
- [x] 3.8 Test with airport-adjacent vs distant hexes
- [x] 3.9 Validate DEN dominance (largest airport)
- [x] 3.10 Document airport accessibility computation

## 4. MUHAA Aggregation and Testing (8 tasks)

- [x] 4.1 Combine hub and airport access: MUHAA = w_hub·A_hub + w_airport·A_airport
- [x] 4.2 Load weights from params.yaml (e.g., 70% hub, 30% airport)
- [x] 4.3 Normalize final MUHAA to 0-100 scale
- [x] 4.4 Integration test on pilot region
- [x] 4.5 Validate MUHAA distributions (urban cores high, rural low)
- [x] 4.6 Compare MUHAA with known regional connectivity patterns
- [x] 4.7 Add MUHAA to total AUCS computation (16% weight)
- [x] 4.8 Generate MUHAA choropleth for QA
