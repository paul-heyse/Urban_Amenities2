# mobility-reliability Specification

## Purpose
Assess the reliability, span, redundancy, and complementary options of local mobility so AUCS reflects transportation resilience.

## Requirements
### Requirement: Five MORR Components
The system SHALL compute the MORR subscore from five components that measure transit quality and supporting mobility.

#### Scenario: C₁ - Frequent transit exposure
- **WHEN** computing C₁
- **THEN** C₁ SHALL measure the percentage of nearby transit stops (<500m) with peak headways under 15 minutes
- **AND** C₁ SHALL be normalized to a 0-100 scale

#### Scenario: C₂ - Service span
- **WHEN** computing C₂
- **THEN** C₂ SHALL measure hours per day with service at nearby stops
- **AND** 24-hour service SHALL score 100 while 12-hour service SHALL score approximately 50

#### Scenario: C₃ - On-time reliability
- **WHEN** GTFS-RT data is available
- **THEN** C₃ SHALL compute the percentage of trips within ±5 minutes of schedule and weight routes by frequency
- **AND** a scheduled-service proxy SHALL be used when GTFS-RT is unavailable

#### Scenario: C₄ - Network redundancy
- **WHEN** computing C₄
- **THEN** C₄ SHALL count unique transit routes and road alternatives as an indicator of resilience

#### Scenario: C₅ - Micromobility presence
- **WHEN** GBFS data exists
- **THEN** C₅ SHALL measure the density of bikeshare or scooter stations within 500 meters
- **AND** areas without micromobility SHALL receive a score of 0

### Requirement: MORR Aggregation
The system SHALL aggregate the five components into the final MORR subscore.

#### Scenario: Weighted sum
- **WHEN** computing MORR
- **THEN** MORR SHALL equal w₁·C₁ + w₂·C₂ + w₃·C₃ + w₄·C₄ + w₅·C₅ with weights configurable in `params.yaml`
- **AND** MORR SHALL be normalized to a 0-100 scale
- **AND** MORR SHALL contribute 12% to the total AUCS score
