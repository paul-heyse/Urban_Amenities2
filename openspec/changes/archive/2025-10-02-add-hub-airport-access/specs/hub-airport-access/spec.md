# Major Urban Hub & Airport Access Specification

## ADDED Requirements

### Requirement: Hub Mass Computation

The system SHALL compute mass scores for major urban hubs based on population, GDP, POI density, and cultural institutions.

#### Scenario: Four mass components

- **WHEN** computing hub mass
- **THEN** components SHALL include: population, GDP, POI count, cultural institutions
- **AND** each component SHALL be normalized to 0-100 scale
- **AND** combined mass SHALL be weighted sum: M = w_pop·Pop + w_gdp·GDP + w_poi·POI + w_culture·Culture

#### Scenario: CBSA definition

- **WHEN** identifying hubs
- **THEN** hubs SHALL be Core-Based Statistical Areas (CBSAs)
- **AND** centroid of CBSA SHALL be used for distance calculation

---

### Requirement: Hub Accessibility

The system SHALL compute accessibility to major hubs weighted by hub mass.

#### Scenario: Best mode selection

- **WHEN** computing hub accessibility
- **THEN** best mode (transit or car) SHALL be selected per OD pair
- **AND** generalized travel cost SHALL be computed

#### Scenario: Mass-weighted decay

- **WHEN** aggregating hub accessibility
- **THEN** formula SHALL be: A_hub = Σ(M_hub · exp(-α · GTC_hub))
- **AND** α SHALL be decay parameter from params.yaml
- **AND** normalization SHALL scale to 0-100

---

### Requirement: Airport Accessibility

The system SHALL compute accessibility to airports weighted by enplanements.

#### Scenario: Enplanement weighting

- **WHEN** computing airport accessibility
- **THEN** airports SHALL be weighted by annual enplanements (passenger volume)
- **AND** larger airports (DEN, SLC) SHALL have greater influence

#### Scenario: Airport access formula

- **WHEN** aggregating airport accessibility
- **THEN** formula SHALL be: A_airport = Σ(Enplane · exp(-α · GTC_airport))
- **AND** normalization SHALL scale to 0-100

---

### Requirement: MUHAA Aggregation

The system SHALL combine hub and airport access into MUHAA subscore.

#### Scenario: Weighted combination

- **WHEN** computing MUHAA
- **THEN** MUHAA = w_hub·A_hub + w_airport·A_airport
- **AND** weights SHALL be configurable (default 70% hub, 30% airport)
- **AND** MUHAA SHALL be normalized to 0-100
- **AND** MUHAA SHALL contribute 16% to total AUCS
