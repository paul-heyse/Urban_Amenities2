# Corridor Trip-Chaining Enrichment Subscore

## Why

CTE rewards locations where you can run errands along transit routes (e.g., grocery + pharmacy on way home from work). 5% weight in AUCS.

## What Changes

- Implement CTE subscore (E34-E35)
- Identify top 2 transit paths from hex to CBD/major hub
- Buffer stops by 350m walking distance
- Score 2-stop errand chains (e.g., grocery + pharmacy)
- Require minimal detour (≤10 min added travel time)
- Bonus for high-quality chain opportunities

## Impact

- Affected specs: `corridor-enrichment` (new)
- Affected code: New `src/Urban_Amenities2/scores/corridor_enrichment.py`
- Dependencies: Requires `add-routing-engines` (OTP2 paths), `add-data-ingestion`
- Mathematical: Implements E34-E35
- Weight: 5% of total AUCS
