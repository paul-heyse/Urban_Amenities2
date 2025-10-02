## ADDED Requirements

### Requirement: PAD-US Public Lands Ingestion

The system SHALL ingest USGS PAD-US protected areas data for parks and open space.

#### Scenario: Download PAD-US geodatabase

- **WHEN** ingesting parks data
- **THEN** the system SHALL download PAD-US 4.x geodatabase or query ArcGIS FeatureServer for CO/UT/ID

#### Scenario: Filter by public access

- **WHEN** loading protected areas
- **THEN** the system SHALL filter to features with Access='Open' and exclude restricted areas

#### Scenario: Compute park access points

- **WHEN** PAD-US polygons are loaded
- **THEN** the system SHALL identify access points (entrances, centroids, or trailheads) for proximity scoring

#### Scenario: Index parks to hexes (area-weighted)

- **WHEN** large parks intersect multiple hexagons
- **THEN** the system SHALL allocate park area to hexes using area-weighted intersection

### Requirement: USFS/NPS Trails Ingestion

The system SHALL ingest trail data from USFS and NPS sources.

#### Scenario: Query USFS EDW trails

- **WHEN** loading trail data
- **THEN** the system SHALL query USFS Enterprise Data Warehouse feature service for National Forest System trails

#### Scenario: Sample trail lines to hexes

- **WHEN** trail LineStrings are loaded
- **THEN** the system SHALL sample points along trails and assign hex_ids for hex-level trail presence

#### Scenario: Load NPS trails and recreation sites

- **WHEN** NPS data is available
- **THEN** the system SHALL ingest via NPS API or RIDB for park-specific trails and facilities

### Requirement: Parks Output Schema

The system SHALL write parks and trails data with hex indexing and attributes.

#### Scenario: Write parks Parquet

- **WHEN** parks processing completes
- **THEN** the output SHALL include: park_id, hex_id, name, designation (National Park, State Park, etc.), area_hectares, access_type
