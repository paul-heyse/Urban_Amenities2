# Leisure & Culture Access Specification

## ADDED Requirements

### Requirement: LCA Subscore Computation

The system SHALL compute Leisure & Culture Access subscore measuring access to non-essential quality-of-life amenities.

#### Scenario: Eight LCA categories

- **WHEN** computing LCA
- **THEN** categories SHALL include: restaurants, cafes, bars, cinemas, performing_arts, museums_galleries, parks_trails, sports_rec
- **AND** each category SHALL be aggregated separately (CES + satiation)
- **AND** cross-category CES SHALL allow substitution between categories

#### Scenario: Cross-category aggregation

- **WHEN** combining LCA categories
- **THEN** cross-category CES SHALL be applied: LCA_raw = (Σ S_c^ρ_LCA)^(1/ρ_LCA)
- **AND** ρ_LCA SHALL be cross-category elasticity parameter
- **AND** normalization SHALL scale to 0-100

---

### Requirement: Novelty Bonus

The system SHALL reward trending or novel venues based on Wikipedia pageview volatility.

#### Scenario: Pageview volatility

- **WHEN** computing novelty bonus
- **THEN** pageview volatility SHALL be computed as std(daily_views) / mean(daily_views)
- **AND** higher volatility SHALL indicate novelty (trending venues)
- **AND** bonus SHALL be 0-20% multiplier on Q_a

#### Scenario: Novelty integration

- **WHEN** applying novelty
- **THEN** novelty-adjusted Q_a SHALL be used before aggregation
- **AND** POIs without pageview data SHALL receive no bonus
