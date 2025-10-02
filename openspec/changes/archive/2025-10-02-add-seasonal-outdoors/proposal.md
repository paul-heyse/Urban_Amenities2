# Seasonal Outdoors Usability Subscore

## Why

SOU adjusts parks/trails accessibility by climate comfort. A park is less valuable if weather is inhospitable most of the year. 5% weight in AUCS.

## What Changes

- Implement SOU subscore (E36)
- Multiply parks/trails accessibility by climate comfort scalar σ_out
- Compute σ_out from NOAA Climate Normals:
  - Comfortable temperature range (50-80°F)
  - Low precipitation (<0.5" per day)
  - Manageable wind (<15 mph)
- Weight by month (growing season vs winter)
- Normalization to 0-100 scale

## Impact

- Affected specs: `seasonal-outdoors` (new)
- Affected code: New `src/Urban_Amenities2/scores/seasonal_outdoors.py`
- Dependencies: Requires `add-data-ingestion` (NOAA, parks), `add-category-aggregation`
- Mathematical: Implements E36
- Weight: 5% of total AUCS
