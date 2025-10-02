# Mobility Options, Reliability & Resilience Subscore

## Why

MORR measures transit quality beyond just travel time: frequency, span, reliability, redundancy, and micromobility options. 12% weight in AUCS.

## What Changes

- Implement MORR subscore (E28-E33) with 5 components:
  1. C₁: Frequent transit exposure (% stops with <15 min headway)
  2. C₂: Service span (hours per day with service)
  3. C₃: On-time reliability (from GTFS-RT delay data)
  4. C₄: Network redundancy (multiple routes, road alternatives)
  5. C₅: Micromobility presence (GBFS bike/scooter availability)
- Weighted sum of components
- Normalization to 0-100 scale

## Impact

- Affected specs: `mobility-reliability` (new)
- Affected code: New `src/Urban_Amenities2/scores/mobility_reliability.py`
- Dependencies: Requires `add-data-ingestion` (GTFS-RT, GBFS), `add-routing-engines`
- Mathematical: Implements E28-E33
- Weight: 12% of total AUCS
