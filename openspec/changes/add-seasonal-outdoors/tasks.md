# Seasonal Outdoors Usability Implementation Tasks

## 1. Climate Comfort Scoring (12 tasks)

- [ ] 1.1 Load NOAA Climate Normals (monthly temp, precip, wind)
- [ ] 1.2 Extract data for stations in/near CO/UT/ID
- [ ] 1.3 Spatially interpolate climate data to hex grid
- [x] 1.4 Define comfortable temperature range (50-80°F)
- [x] 1.5 Compute temperature comfort score per month (0-1 scale)
- [x] 1.6 Define precipitation threshold (<0.5" per day comfortable)
- [x] 1.7 Compute precipitation comfort score per month
- [x] 1.8 Define wind threshold (<15 mph manageable)
- [x] 1.9 Compute wind comfort score per month
- [x] 1.10 Combine components: σ_month = temp_comfort · precip_comfort · wind_comfort
- [x] 1.11 Weight months by season (growing season > winter)
- [x] 1.12 Compute annual climate comfort: σ_out = Σ(w_month · σ_month)

## 2. Parks/Trails Accessibility (8 tasks)

- [ ] 2.1 Load parks/trails POIs from data ingestion
- [ ] 2.2 Compute accessibility to parks/trails (w_ia from travel time)
- [ ] 2.3 Apply quality scores to parks (size, amenities, designation)
- [ ] 2.4 Aggregate parks/trails accessibility using CES + satiation
- [ ] 2.5 Obtain base parks/trails score (before climate adjustment)
- [ ] 2.6 Test base score with known park-rich vs park-poor areas
- [ ] 2.7 Validate base score in [0, 100]
- [ ] 2.8 Document parks/trails scoring

## 3. SOU Computation (7 tasks)

- [x] 3.1 Multiply parks/trails score by climate comfort: SOU = Parks_score · σ_out
- [x] 3.2 Normalize SOU to 0-100 scale
- [x] 3.3 Handle hexes with no parks (SOU=0)
- [ ] 3.4 Validate SOU distributions (mountain regions vs deserts)
- [ ] 3.5 Integration test on pilot region
- [ ] 3.6 Add SOU to total AUCS computation (5% weight)
- [ ] 3.7 Generate SOU choropleth for QA

## 4. Testing and Validation (8 tasks)

- [ ] 4.1 Unit test climate comfort scoring (known temp/precip/wind)
- [ ] 4.2 Test with extreme climates (Colorado mountains, Utah deserts)
- [ ] 4.3 Validate σ_out in [0, 1] range
- [ ] 4.4 Compare SOU with known outdoor recreation areas
- [ ] 4.5 Validate SOU penalizes areas with harsh winters or hot summers
- [ ] 4.6 Property test: SOU in [0, 100]
- [ ] 4.7 Compare SOU with/without climate adjustment
- [ ] 4.8 Document SOU methodology and climate parameters
