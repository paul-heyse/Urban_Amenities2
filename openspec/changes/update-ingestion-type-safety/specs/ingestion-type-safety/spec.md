## ADDED Requirements
### Requirement: Ingestion Pipeline Type Safety
External data ingestion modules SHALL expose typed interfaces covering BigQuery, HTTP enrichment, and GTFS realtime fallbacks.

#### Scenario: Typed BigQuery/Oustream ingestion
- **WHEN** `mypy src/Urban_Amenities2/io/overture --warn-unused-ignores` runs
- **THEN** BigQuery clients and shapely conversions SHALL succeed without assigning `None` to typed modules or returning `Any` DataFrames.

#### Scenario: Typed HTTP enrichment clients
- **WHEN** parks and Wikipedia ingestion utilities are type checked
- **THEN** request parameter dictionaries SHALL match `requests` expectations and response parsing SHALL return typed dataclasses or DataFrames.

#### Scenario: Typed GTFS realtime fallbacks
- **WHEN** GTFS realtime fallback serializer/deserializer is type checked
- **THEN** the code SHALL return concrete `bytes` payloads and structured record objects with no implicit `Any` operations.
