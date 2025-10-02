## ADDED Requirements

### Requirement: Overture Places Ingestion

The system SHALL ingest Overture Maps Places data and map it to AUCS categories.

#### Scenario: Load Places from BigQuery

- **WHEN** ingesting Overture Places via BigQuery for Colorado bounding box
- **THEN** the system SHALL query the Overture public dataset, filter by state bounds, and return GeoDataFrame with places

#### Scenario: Load Places from S3/Azure

- **WHEN** ingesting from Overture Parquet files on cloud storage
- **THEN** the system SHALL read partitioned GeoParquet, filter by bbox, and return places

#### Scenario: Filter by operating status

- **WHEN** loading places
- **THEN** the system SHALL exclude places where operating_status is not 'open'

### Requirement: Category Crosswalk

The system SHALL map Overture categories to AUCS amenity types using prefix matching rules.

#### Scenario: Map restaurant categories

- **WHEN** a place has category `eat_and_drink.restaurant.italian_restaurant`
- **THEN** the system SHALL assign aucstype='restaurants_full_service'

#### Scenario: Exclude fast food from restaurants

- **WHEN** a place has category `eat_and_drink.fast_food`
- **THEN** the system SHALL assign aucstype='fast_food_quick', not 'restaurants_full_service'

#### Scenario: Handle multiple categories

- **WHEN** a place has both primary and alternate categories
- **THEN** the system SHALL use the primary category for aucstype, falling back to alternates if primary is unmapped

### Requirement: POI Deduplication

The system SHALL deduplicate POIs within hexagons using brand, name, and proximity.

#### Scenario: Remove duplicate chains

- **WHEN** multiple POIs with the same brand (e.g., "Starbucks") appear within 50m in a hex
- **THEN** the system SHALL keep only one instance and apply brand deduplication weight (E8)

#### Scenario: Fuzzy name matching

- **WHEN** two POIs have similar names ("Joe's Coffee" vs "Joe's Cafe") at nearly the same coordinates
- **THEN** the system SHALL merge them if name similarity > 0.85 and distance < 25m

### Requirement: H3 Hex Indexing of POIs

The system SHALL assign H3 resolution 9 hex_id to all POIs.

#### Scenario: Index POI to containing hex

- **WHEN** a POI has lat/lon coordinates
- **THEN** the system SHALL compute and store the H3 r=9 cell as hex_id

### Requirement: POI Output Schema

The system SHALL write deduplicated, hex-indexed POIs to Parquet with required fields.

#### Scenario: Write POI Parquet

- **WHEN** POI processing completes
- **THEN** the output SHALL include: poi_id, hex_id, aucstype, name, brand, brand_wd (Wikidata), lat, lon, confidence, opening_hours, quality_attrs
