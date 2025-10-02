# Amenity Quality Specification

## ADDED Requirements

### Requirement: Destination Quality Scoring

The system SHALL compute quality scores Q_a for all POIs based on size, popularity, brand, and heritage.

#### Scenario: Size/capacity scoring

- **WHEN** computing Q_a for POI
- **THEN** size SHALL be scored from available attributes (square footage, seating capacity, collection size)
- **AND** larger venues SHALL receive higher scores (with diminishing returns)
- **AND** missing size data SHALL use category median

#### Scenario: Popularity scoring

- **WHEN** Wikipedia pageview data is available
- **THEN** pageviews SHALL be normalized to 0-100 scale per category
- **AND** higher pageviews SHALL indicate higher quality
- **AND** POIs without Wikipedia SHALL receive neutral popularity score

#### Scenario: Combined Q_a score

- **WHEN** computing total Q_a
- **THEN** components SHALL be combined with weights: size=30%, popularity=40%, brand=15%, heritage=15%
- **AND** final Q_a SHALL be in range [0, 100]
- **AND** Q_a SHALL be stored in POI data for accessibility computation

---

### Requirement: Brand-Proximity Deduplication

The system SHALL reduce weights for same-brand POIs in close proximity to avoid overcounting chains.

#### Scenario: Same-brand identification

- **WHEN** identifying brand chains
- **THEN** Wikidata brand property SHALL be used if available
- **AND** name matching SHALL be fallback (e.g., "Starbucks" in name)
- **AND** independent businesses SHALL not be penalized

#### Scenario: Proximity penalty

- **WHEN** two same-brand POIs are within 500m
- **THEN** weight reduction SHALL be applied: w' = w × (1 - exp(-d/500))
- **AND** more distant pairs SHALL have less penalty
- **AND** total category weight SHALL be preserved

---

### Requirement: Opening Hours Bonus

The system SHALL increase Q_a for POIs with extended or 24/7 hours.

#### Scenario: Hours classification

- **WHEN** POI has opening hours data
- **THEN** hours SHALL be classified: 24/7, extended (>12h/day), standard (<12h/day), limited (<6h/day)
- **AND** 24/7 receives 20% bonus, extended 10%, standard 0%, limited -10%

#### Scenario: Missing hours data

- **WHEN** opening hours are missing
- **THEN** category default hours SHALL be assumed (e.g., grocery standard, bar extended)
