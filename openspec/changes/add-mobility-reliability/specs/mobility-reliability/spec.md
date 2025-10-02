# Mobility Options, Reliability & Resilience Specification

## ADDED Requirements

### Requirement: Five MORR Components

The system SHALL compute MORR subscore from five components measuring transit quality.

#### Scenario: C₁ - Frequent transit exposure

- **WHEN** computing C₁
- **THEN** C₁ SHALL measure % of nearby transit stops (<500m) with <15 min peak headway
- **AND** C₁ SHALL be normalized to 0-100 scale

#### Scenario: C₂ - Service span

- **WHEN** computing C₂
- **THEN** C₂ SHALL measure hours per day with service at nearby stops
- **AND** 24-hour service SHALL score 100, 12-hour SHALL score ~50

#### Scenario: C₃ - On-time reliability

- **WHEN** GTFS-RT data is available
- **THEN** C₃ SHALL compute % of trips within ±5 min of schedule
- **AND** routes SHALL be weighted by frequency
- **AND** C₃ SHALL use fallback if GTFS-RT unavailable

#### Scenario: C₄ - Network redundancy

- **WHEN** computing C₄
- **THEN** C₄ SHALL count unique transit routes and road alternatives
- **AND** higher route counts SHALL indicate greater resilience

#### Scenario: C₅ - Micromobility presence

- **WHEN** GBFS data exists
- **THEN** C₅ SHALL measure density of bikeshare/scooter stations (<500m)
- **AND** areas without micromobility SHALL score 0

---

### Requirement: MORR Aggregation

The system SHALL aggregate components into final MORR subscore.

#### Scenario: Weighted sum

- **WHEN** computing MORR
- **THEN** MORR = w₁·C₁ + w₂·C₂ + w₃·C₃ + w₄·C₄ + w₅·C₅
- **AND** weights SHALL be configurable in params.yaml
- **AND** MORR SHALL be normalized to 0-100
- **AND** MORR SHALL contribute 12% to total AUCS
