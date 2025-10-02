# Corridor Trip-Chaining Enrichment Specification

## ADDED Requirements

### Requirement: Transit Path Identification

The system SHALL identify top transit paths from each hex to major hubs.

#### Scenario: Major hub definition

- **WHEN** identifying paths
- **THEN** major hubs SHALL include: downtown cores, employment centers, universities
- **AND** hubs SHALL be defined per metro area

#### Scenario: Top 2 paths

- **WHEN** computing CTE for hex
- **THEN** top 2 paths SHALL be selected by frequency and directness
- **AND** paths with <5 stops SHALL be excluded (too short)

---

### Requirement: Errand Chain Scoring

The system SHALL score 2-stop errand chains along transit corridors.

#### Scenario: Stop buffering

- **WHEN** collecting POIs along path
- **THEN** each stop SHALL be buffered by 350m walking distance
- **AND** POIs within buffer SHALL be candidate errand stops

#### Scenario: Feasible chains

- **WHEN** identifying chains
- **THEN** common chains SHALL include: grocery+pharmacy, bank+post, grocery+childcare
- **AND** detour time SHALL be computed (vs direct trip)
- **AND** chains with detour >10 min SHALL be excluded

#### Scenario: Chain quality

- **WHEN** scoring chains
- **THEN** chain quality SHALL be product of both amenities' Q_a
- **AND** chain likelihood SHALL weight score (frequent vs rare combinations)

---

### Requirement: CTE Aggregation

The system SHALL aggregate chain opportunities into CTE subscore.

#### Scenario: CTE normalization

- **WHEN** computing CTE
- **THEN** all feasible chains SHALL be aggregated
- **AND** CTE SHALL be normalized to 0-100 scale
- **AND** CTE SHALL contribute 5% to total AUCS
