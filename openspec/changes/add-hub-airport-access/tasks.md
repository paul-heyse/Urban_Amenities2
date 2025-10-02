# Major Urban Hub & Airport Access Implementation Tasks

## 1. Hub Mass Calculation (12 tasks)

- [ ] 1.1 Load CBSA (Core-Based Statistical Area) boundaries
- [ ] 1.2 Load population data per CBSA (Census)
- [ ] 1.3 Load GDP data per CBSA (BEA Regional Economic Accounts)
- [ ] 1.4 Count POIs per CBSA from Overture data
- [ ] 1.5 Count cultural institutions per CBSA (museums, theaters, universities)
- [ ] 1.6 Normalize each mass component to 0-100 scale
- [ ] 1.7 Compute combined hub mass: M = w_pop·Pop + w_gdp·GDP + w_poi·POI + w_culture·Culture
- [ ] 1.8 Load component weights from params.yaml
- [ ] 1.9 Validate mass scores for known hubs (Denver > Pueblo)
- [ ] 1.10 Store hub mass in reference table
- [ ] 1.11 Test with all CBSAs in CO/UT/ID
- [ ] 1.12 Document hub mass methodology

## 2. Hub Accessibility (10 tasks)

- [ ] 2.1 Compute travel times from each hex to each CBSA centroid
- [ ] 2.2 Use best mode (transit or car) per OD pair
- [ ] 2.3 Compute generalized travel cost (GTC) for each hub
- [ ] 2.4 Apply decay function: A_hub = Σ(M_hub · exp(-α · GTC_hub))
- [ ] 2.5 Load decay parameter α from params.yaml
- [ ] 2.6 Normalize hub accessibility to 0-100 scale
- [ ] 2.7 Test with central vs peripheral hexes
- [ ] 2.8 Validate hub accessibility correlates with regional connectivity
- [ ] 2.9 Handle hexes with no reachable hubs (score=0)
- [ ] 2.10 Document hub accessibility computation

## 3. Airport Accessibility (10 tasks)

- [ ] 3.1 Load FAA airport enplanement data (annual passengers)
- [ ] 3.2 Filter to airports in/near CO/UT/ID (DEN, SLC, BOI, COS, etc.)
- [ ] 3.3 Compute travel times from each hex to each airport
- [ ] 3.4 Use best mode (car typically; transit if available)
- [ ] 3.5 Compute GTC for each airport
- [ ] 3.6 Apply decay with enplanement weighting: A_airport = Σ(Enplane · exp(-α · GTC))
- [ ] 3.7 Normalize airport accessibility to 0-100 scale
- [ ] 3.8 Test with airport-adjacent vs distant hexes
- [ ] 3.9 Validate DEN dominance (largest airport)
- [ ] 3.10 Document airport accessibility computation

## 4. MUHAA Aggregation and Testing (8 tasks)

- [ ] 4.1 Combine hub and airport access: MUHAA = w_hub·A_hub + w_airport·A_airport
- [ ] 4.2 Load weights from params.yaml (e.g., 70% hub, 30% airport)
- [ ] 4.3 Normalize final MUHAA to 0-100 scale
- [ ] 4.4 Integration test on pilot region
- [ ] 4.5 Validate MUHAA distributions (urban cores high, rural low)
- [ ] 4.6 Compare MUHAA with known regional connectivity patterns
- [ ] 4.7 Add MUHAA to total AUCS computation (16% weight)
- [ ] 4.8 Generate MUHAA choropleth for QA
