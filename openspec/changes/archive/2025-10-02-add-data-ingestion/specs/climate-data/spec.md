## ADDED Requirements

### Requirement: NOAA Climate Normals Ingestion

The system SHALL download and process NOAA 1991-2020 climate normals for outdoor comfort scoring.

#### Scenario: Query NOAA NCEI API

- **WHEN** fetching monthly normals for CO/UT/ID stations
- **THEN** the system SHALL use the Access Data Service API with dataset='normals-monthly-1991-2020'

#### Scenario: Extract temperature and precipitation

- **WHEN** normals data is returned
- **THEN** the system SHALL extract monthly mean temperature, precipitation, and optionally wind/snow

#### Scenario: Interpolate to hex grid

- **WHEN** station-based normals are loaded
- **THEN** the system SHALL interpolate values to H3 r=9 hexes using nearest-station or inverse-distance weighting

### Requirement: Outdoor Comfort Scoring

The system SHALL compute monthly outdoor comfort scalars (σ_out) from climate normals.

#### Scenario: Define comfortable conditions

- **WHEN** computing outdoor usability
- **THEN** the system SHALL classify days as comfortable if: 10°C ≤ Tmean ≤ 27°C, precip_prob < 40%, wind < 8 m/s

#### Scenario: Compute monthly scalars

- **WHEN** monthly normals are processed
- **THEN** the system SHALL output σ_out ∈ [0,1] per hex per month representing fraction of comfortable days

#### Scenario: Handle missing climate data

- **WHEN** a hex has no nearby weather stations
- **THEN** the system SHALL use regional defaults or flag as missing with σ_out = 1.0 (neutral)
