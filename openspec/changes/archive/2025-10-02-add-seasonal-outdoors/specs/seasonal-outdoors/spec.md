# Seasonal Outdoors Usability Specification

## ADDED Requirements

### Requirement: Climate Comfort Scoring

The system SHALL compute climate comfort scalar σ_out from NOAA Climate Normals.

#### Scenario: Temperature comfort

- **WHEN** computing temperature comfort
- **THEN** comfortable range SHALL be 50-80°F
- **AND** months outside range SHALL have reduced comfort score
- **AND** comfort SHALL be computed per month

#### Scenario: Precipitation comfort

- **WHEN** computing precipitation comfort
- **THEN** threshold SHALL be <0.5" per day
- **AND** higher precipitation SHALL reduce comfort

#### Scenario: Wind comfort

- **WHEN** computing wind comfort
- **THEN** threshold SHALL be <15 mph
- **AND** higher wind SHALL reduce comfort

#### Scenario: Monthly aggregation

- **WHEN** combining monthly comfort
- **THEN** annual comfort SHALL be: σ_out = Σ(w_month · σ_month)
- **AND** months SHALL be weighted by season (growing season > winter)
- **AND** σ_out SHALL be in range [0, 1]

---

### Requirement: SOU Subscore Computation

The system SHALL compute SOU by adjusting parks/trails accessibility by climate comfort.

#### Scenario: Climate adjustment

- **WHEN** computing SOU
- **THEN** SOU = Parks_score · σ_out
- **AND** parks/trails score SHALL be computed via CES + satiation
- **AND** climate comfort SHALL multiply final score

#### Scenario: SOU normalization

- **WHEN** normalizing SOU
- **THEN** SOU SHALL be scaled to 0-100
- **AND** SOU SHALL contribute 5% to total AUCS
- **AND** hexes with no parks SHALL score 0
