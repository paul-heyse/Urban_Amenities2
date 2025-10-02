# leisure-culture-access Specification

## Purpose
Measure access to leisure and cultural amenities, capturing breadth and novelty so AUCS reflects quality-of-life destinations.

## Requirements
### Requirement: LCA Subscore Computation
The system SHALL compute the Leisure & Culture Access (LCA) subscore to represent non-essential amenities.

#### Scenario: Eight LCA categories
- **WHEN** computing LCA
- **THEN** the categories SHALL include restaurants, cafes, bars, cinemas, performing_arts, museums_galleries, parks_trails, and sports_rec
- **AND** each category SHALL be aggregated with CES plus satiation
- **AND** cross-category CES SHALL allow substitution between categories

#### Scenario: Cross-category aggregation
- **WHEN** combining category scores
- **THEN** cross-category CES SHALL be applied as LCA_raw = (Σ S_c^ρ_LCA)^(1/ρ_LCA)
- **AND** ρ_LCA SHALL be the elasticity parameter configured for LCA
- **AND** results SHALL be normalized to a 0-100 scale

### Requirement: Novelty Bonus
The system SHALL reward trending or novel venues using Wikipedia pageview volatility.

#### Scenario: Pageview volatility
- **WHEN** computing the novelty bonus
- **THEN** volatility SHALL be std(daily_views) / mean(daily_views)
- **AND** higher volatility SHALL translate to a 0-20% multiplier applied as a bonus

#### Scenario: Novelty integration
- **WHEN** applying novelty to POI quality
- **THEN** novelty-adjusted Q_a SHALL be used before aggregation
- **AND** POIs without pageview data SHALL receive no bonus
