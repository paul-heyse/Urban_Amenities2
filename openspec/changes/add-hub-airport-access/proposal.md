# Major Urban Hub & Airport Access Subscore

## Why

MUHAA measures connectivity to major employment/activity centers and airports. Important for regional connectivity and economic access. 16% weight in AUCS.

## What Changes

- Implement MUHAA subscore (E19-E25) with two components:
  1. Hub access: Accessibility to CBSAs weighted by mass (population, GDP, POI density, culture)
  2. Airport access: Accessibility to airports weighted by enplanements
- Hub mass calculation (E20-E22): population, GDP, POI count, cultural institutions
- Best mode selection (transit or car) per destination
- Decay by generalized travel cost
- Normalization to 0-100 scale

## Impact

- Affected specs: `hub-airport-access` (new)
- Affected code: New `src/Urban_Amenities2/scores/hub_airport_access.py`
- Dependencies: Requires `add-travel-time-computation`, `add-data-ingestion` (FAA, BEA/Census)
- Mathematical: Implements E19-E25
- Weight: 16% of total AUCS
