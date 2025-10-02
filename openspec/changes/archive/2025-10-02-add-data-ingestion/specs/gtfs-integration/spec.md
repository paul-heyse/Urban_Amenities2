## ADDED Requirements

### Requirement: GTFS Agency Registry

The system SHALL maintain a registry of transit agencies for Colorado, Utah, and Idaho.

#### Scenario: Load agency registry

- **WHEN** initializing GTFS ingestion
- **THEN** the system SHALL load agency metadata (name, state, modes, static_url, rt_urls, license) from configuration

#### Scenario: Discover agencies via Transitland

- **WHEN** building or updating the registry
- **THEN** the system SHALL query Transitland API for feeds in CO/UT/ID and populate agency records

### Requirement: GTFS Static Feed Download

The system SHALL download and cache GTFS zip files for each agency.

#### Scenario: Download GTFS feed

- **WHEN** an agency's static GTFS URL is provided
- **THEN** the system SHALL download the zip, validate structure, and cache it with version/date metadata

#### Scenario: Detect feed updates

- **WHEN** a feed's ETag or last-modified date changes
- **THEN** the system SHALL download the new version and track the change

### Requirement: GTFS Parsing and Validation

The system SHALL parse GTFS feeds using partridge and validate against GTFS spec.

#### Scenario: Parse required files

- **WHEN** a GTFS zip is loaded
- **THEN** the system SHALL extract stops.txt, routes.txt, trips.txt, stop_times.txt, calendar.txt

#### Scenario: Handle optional files

- **WHEN** frequencies.txt or transfers.txt are present
- **THEN** the system SHALL parse them for headway and transfer penalty data

#### Scenario: Validation errors

- **WHEN** a GTFS feed has missing required fields or invalid values
- **THEN** the system SHALL log validation errors and skip malformed records

### Requirement: Transit Stops Hex Indexing

The system SHALL index GTFS stops to H3 hexagons.

#### Scenario: Assign hex_id to stops

- **WHEN** stops.txt contains stop_lat/stop_lon
- **THEN** the system SHALL compute H3 r=9 hex_id for each stop

#### Scenario: Group stops by parent station

- **WHEN** stops have parent_station defined
- **THEN** the system SHALL group platform-level stops under the parent for hierarchy

### Requirement: Headway and Service Span Computation

The system SHALL compute service frequency and span from GTFS schedules.

#### Scenario: Compute headways from stop_times

- **WHEN** frequencies.txt is absent
- **THEN** the system SHALL derive headways by counting departures per hour per route per stop

#### Scenario: Use frequencies.txt when available

- **WHEN** frequencies.txt defines headway-based service
- **THEN** the system SHALL use exact_times and headway_secs for frequency metrics

#### Scenario: Compute service span by time slice

- **WHEN** calendar.txt and stop_times.txt are parsed
- **THEN** the system SHALL compute hours of service per day by time slice (WD_AM, WD_MD, etc.)

### Requirement: GTFS Realtime Ingestion

The system SHALL fetch and parse GTFS-RT feeds for reliability metrics.

#### Scenario: Fetch TripUpdates

- **WHEN** an agency provides GTFS-RT TripUpdates endpoint
- **THEN** the system SHALL poll the feed, parse protobuf, and extract delay information

#### Scenario: Fetch VehiclePositions

- **WHEN** an agency provides VehiclePositions
- **THEN** the system SHALL parse vehicle lat/lon, timestamps, and trip associations

#### Scenario: Compute on-time performance

- **WHEN** TripUpdates contain delay at timepoints
- **THEN** the system SHALL compute percent on-time (delay <= 5 min) and mean absolute delay

#### Scenario: Compute headway adherence

- **WHEN** VehiclePositions are available
- **THEN** the system SHALL compute actual headway variance vs scheduled headway
