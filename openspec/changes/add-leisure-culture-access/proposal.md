# Leisure & Culture Access Subscore

## Why

LCA measures access to non-essential amenities that enhance quality of life: restaurants, cafes, bars, entertainment, parks, sports. 18% weight in total AUCS.

## What Changes

- Implement LCA subscore (E16-E18) with 8 categories:
  - Restaurants, cafes, bars
  - Cinemas, performing arts
  - Museums, galleries
  - Parks, trails
  - Sports, recreation
- Cross-category CES aggregation (allows substitution between categories)
- Novelty bonus (E18) from Wikipedia pageview volatility (trending venues scored higher)
- Normalization to 0-100 scale

## Impact

- Affected specs: `leisure-culture-access` (new)
- Affected code: New `src/Urban_Amenities2/scores/leisure_culture_access.py`
- Dependencies: Requires `add-category-aggregation`
- Mathematical: Implements E16-E18
- Weight: 18% of total AUCS
