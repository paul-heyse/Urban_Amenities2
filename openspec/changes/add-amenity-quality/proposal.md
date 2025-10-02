# Amenity Quality Scoring

## Why

AUCS scores depend on destination quality (Q_a). Raw POI counts don't capture that a flagship grocery store is more valuable than a corner store, or that a heritage museum is more valuable than a small gallery.

## What Changes

- Implement destination quality scoring Q_a (E6-E9)
- Size/capacity scoring (square footage, seating, collection size)
- Popularity scoring (Wikipedia pageviews, social media)
- Brand recognition and heritage flags (Wikidata properties)
- Brand-proximity deduplication (E8) - reduce weight for chains near each other
- Opening hours bonus (24/7 > extended > limited hours)

## Impact

- Affected specs: `amenity-quality` (new)
- Affected code: New `src/Urban_Amenities2/quality/` module
- Dependencies: Requires `add-data-ingestion` (Wikidata, Wikipedia enrichment)
- Mathematical: Implements E6-E9 from spec
