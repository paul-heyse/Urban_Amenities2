# hub-airport-access Specification

## Purpose
Quantify access to major urban hubs and airports so AUCS captures regional connectivity to large-scale economic centers.

## Requirements
### Requirement: Hub Mass Computation
The system SHALL compute mass scores for major urban hubs based on population, GDP, POI density, and cultural institutions.

#### Scenario: Four mass components
- **WHEN** computing hub mass
- **THEN** components SHALL include population, GDP, POI count, and cultural institutions
- **AND** each component SHALL be normalized to a 0-100 scale
- **AND** the combined mass SHALL be M = w_pop·Pop + w_gdp·GDP + w_poi·POI + w_culture·Culture

#### Scenario: CBSA definition
- **WHEN** identifying hubs
- **THEN** hubs SHALL correspond to Core-Based Statistical Areas (CBSAs)
- **AND** the CBSA centroid SHALL be used for distance calculation

### Requirement: Hub Accessibility
The system SHALL compute accessibility to major hubs weighted by hub mass.

#### Scenario: Best mode selection
- **WHEN** computing hub accessibility
- **THEN** the best mode (transit or car) SHALL be selected per origin-destination pair
- **AND** a generalized travel cost SHALL be computed for the chosen mode

#### Scenario: Mass-weighted decay
- **WHEN** aggregating hub accessibility
- **THEN** hub accessibility SHALL be A_hub = Σ(M_hub · exp(-α · GTC_hub))
- **AND** α SHALL be a decay parameter sourced from `params.yaml`
- **AND** results SHALL be normalized to a 0-100 scale

### Requirement: Airport Accessibility
The system SHALL compute accessibility to airports weighted by enplanements.

#### Scenario: Enplanement weighting
- **WHEN** computing airport accessibility
- **THEN** airports SHALL be weighted by annual enplanements so higher-volume airports have greater influence

#### Scenario: Airport access formula
- **WHEN** aggregating airport accessibility
- **THEN** airport accessibility SHALL be A_airport = Σ(Enplane · exp(-α · GTC_airport))
- **AND** results SHALL be normalized to a 0-100 scale

### Requirement: MUHAA Aggregation
The system SHALL combine hub and airport access into the MUHAA subscore.

#### Scenario: Weighted combination
- **WHEN** computing MUHAA
- **THEN** MUHAA SHALL be w_hub·A_hub + w_airport·A_airport with configurable weights (default 70% hub, 30% airport)
- **AND** MUHAA SHALL be normalized to a 0-100 scale
- **AND** MUHAA SHALL contribute 16% to the total AUCS score
