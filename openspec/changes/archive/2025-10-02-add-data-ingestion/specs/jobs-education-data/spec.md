## ADDED Requirements

### Requirement: LODES Jobs Data Ingestion

The system SHALL ingest LEHD LODES employment data for jobs accessibility scoring.

#### Scenario: Download LODES WAC files

- **WHEN** loading jobs data for Colorado
- **THEN** the system SHALL download LODES v8 Workplace Area Characteristic (WAC) files from LEHD

#### Scenario: Parse block-level job counts

- **WHEN** WAC CSVs are loaded
- **THEN** the system SHALL extract job counts by Census block and NAICS sector

#### Scenario: Geocode Census blocks

- **WHEN** allocating jobs to hexes
- **THEN** the system SHALL use TIGER/Line block centroids or area-weighted allocation to H3 r=9 hexes

#### Scenario: Write jobs by hex

- **WHEN** jobs processing completes
- **THEN** the output SHALL include: hex_id, total_jobs, jobs_by_sector (NAICS 2-digit), data_year

### Requirement: NCES Schools Data Ingestion

The system SHALL ingest public and private school data from NCES.

#### Scenario: Download CCD and PSS

- **WHEN** loading school data
- **THEN** the system SHALL download NCES Common Core of Data (public schools) and Private School Survey

#### Scenario: Geocode schools

- **WHEN** NCES data is loaded
- **THEN** the system SHALL use NCES EDGE geocodes for lat/lon coordinates

#### Scenario: Extract school attributes

- **WHEN** computing school quality proxies
- **THEN** the system SHALL extract: enrollment, student_teacher_ratio, grade_span, school_type

#### Scenario: Index schools to hexes

- **WHEN** schools are geocoded
- **THEN** the system SHALL assign H3 r=9 hex_ids and write schools.parquet

### Requirement: IPEDS Universities Data Ingestion

The system SHALL ingest university data with Carnegie classifications for higher education access scoring.

#### Scenario: Download IPEDS directory

- **WHEN** loading university data
- **THEN** the system SHALL download IPEDS institutional directory with coordinates

#### Scenario: Load Carnegie classifications

- **WHEN** assigning university quality weights
- **THEN** the system SHALL load Carnegie 2021 classification data (R1, R2, Doctoral, etc.)

#### Scenario: Compute quality weights

- **WHEN** universities are loaded
- **THEN** the system SHALL assign q_u weights: R1=1.0, R2=0.7, Doctoral=0.4, others=0.2

#### Scenario: Write universities Parquet

- **WHEN** processing completes
- **THEN** the output SHALL include: univ_id, hex_id, name, carnegie_tier, q_u, enrollment

### Requirement: State Childcare Registry Ingestion

The system SHALL ingest licensed childcare providers from state registries for CO, UT, and ID.

#### Scenario: Load Colorado childcare

- **WHEN** ingesting CO childcare data
- **THEN** the system SHALL query CDPHE ArcGIS Feature Layer for licensed providers

#### Scenario: Load Utah and Idaho childcare

- **WHEN** state-level geocoded APIs are unavailable
- **THEN** the system SHALL use Overture Places childcare category supplemented by manual registry exports

#### Scenario: Extract capacity and license type

- **WHEN** available in state data
- **THEN** the system SHALL record capacity and license_type for quality weighting
