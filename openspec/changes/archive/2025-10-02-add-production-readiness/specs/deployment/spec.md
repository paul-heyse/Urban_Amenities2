# Deployment Specification

## ADDED Requirements

### Requirement: OSRM Service Deployment

The system SHALL deploy and maintain OSRM routing services for all required profiles.

#### Scenario: OSRM graphs are built from Overture data

- **WHEN** deploying OSRM services
- **THEN** Overture Transportation segments SHALL be converted to OSM-compatible format
- **AND** three profiles SHALL be built: car, bike, foot
- **AND** graph build SHALL complete without errors

#### Scenario: OSRM services are accessible

- **WHEN** application initializes
- **THEN** OSRM services SHALL respond to health checks within 5 seconds
- **AND** service URLs SHALL be configured via environment variables (OSRM_CAR_URL, OSRM_BIKE_URL, OSRM_FOOT_URL)
- **AND** unreachable services SHALL cause application to fail fast with clear error

#### Scenario: OSRM services handle expected load

- **WHEN** processing full 3-state dataset
- **THEN** OSRM SHALL handle at least 100 requests/second per profile
- **AND** response times SHALL be <500ms for /table queries (p95)
- **AND** services SHALL NOT run out of memory or crash

#### Scenario: OSRM graphs are versioned

- **WHEN** rebuilding OSRM graphs
- **THEN** graph version SHALL be recorded in run manifest
- **AND** old graphs SHALL be archived for reproducibility
- **AND** graph rebuild procedure SHALL be documented

#### Scenario: OSRM errors are handled gracefully

- **WHEN** OSRM returns "No route found"
- **THEN** application SHALL set travel time to infinity (unreachable)
- **AND** SHALL continue processing other OD pairs
- **AND** SHALL log failure with origin/destination coordinates

---

### Requirement: OpenTripPlanner 2 Service Deployment

The system SHALL deploy and maintain OTP2 service for transit routing.

#### Scenario: OTP2 graph is built from GTFS and streets

- **WHEN** deploying OTP2
- **THEN** all valid GTFS feeds from CO/UT/ID SHALL be included
- **AND** Overture street network SHALL be included
- **AND** graph build SHALL validate all feeds and log errors
- **AND** graph SHALL be saved to persistent storage

#### Scenario: OTP2 service is accessible

- **WHEN** application initializes
- **THEN** OTP2 GraphQL endpoint SHALL respond to health checks within 10 seconds
- **AND** service URL SHALL be configured via environment variable (OTP_URL)
- **AND** unreachable service SHALL cause application to fail fast with clear error

#### Scenario: OTP2 service handles expected load

- **WHEN** processing transit accessibility queries
- **THEN** OTP2 SHALL handle at least 20 complex queries/second
- **AND** query response times SHALL be <2 seconds (p95)
- **AND** service SHALL have at least 8GB RAM allocated (per region graph)

#### Scenario: OTP2 graph is refreshed regularly

- **WHEN** GTFS feeds are updated
- **THEN** graph SHALL be rebuilt within 24 hours
- **AND** rebuild SHALL be automated (cron or orchestrator)
- **AND** old graph SHALL be backed up before replacement
- **AND** graph version SHALL be recorded in run manifest

#### Scenario: OTP2 GraphQL errors are handled

- **WHEN** OTP2 returns GraphQL errors
- **THEN** application SHALL parse error messages
- **AND** SHALL retry transient errors (max 3 times with backoff)
- **AND** SHALL fall back to non-transit modes if transit unavailable
- **AND** SHALL log full error context

---

### Requirement: External API Configuration

The system SHALL securely configure and access external APIs.

#### Scenario: API credentials are stored securely

- **WHEN** configuring external APIs
- **THEN** API keys SHALL be stored in secrets manager or environment variables
- **AND** SHALL NOT be committed to git
- **AND** SHALL be rotated quarterly
- **AND** access SHALL be audited

#### Scenario: API rate limits are respected

- **WHEN** calling Wikipedia or Wikidata APIs
- **THEN** application SHALL implement rate limiting (max 100 req/sec for Wikipedia, 10 req/sec for Wikidata)
- **AND** SHALL implement exponential backoff on 429 errors
- **AND** SHALL log rate limit events

#### Scenario: API failures have fallbacks

- **WHEN** external API is unavailable (timeout, 503)
- **THEN** application SHALL use cached data if available
- **AND** SHALL skip optional enrichments if cache miss
- **AND** SHALL log API unavailability
- **AND** SHALL continue processing

#### Scenario: API responses are cached

- **WHEN** fetching data from external APIs
- **THEN** responses SHALL be cached with TTL (24 hours for Wikipedia pageviews, 7 days for Wikidata)
- **AND** cache SHALL be persistent (disk-based)
- **AND** cache size SHALL be limited (max 10GB)

---

### Requirement: Container Deployment

The system SHALL be deployable as a containerized application.

#### Scenario: Production Dockerfile is optimized

- **WHEN** building production container
- **THEN** multi-stage build SHALL be used (build stage + runtime stage)
- **AND** dependencies SHALL be pinned to specific versions
- **AND** container SHALL use non-root user
- **AND** container size SHALL be <2GB

#### Scenario: Container configuration via environment

- **WHEN** running container
- **THEN** all configuration SHALL be injectable via environment variables
- **AND** secrets SHALL NOT be baked into image
- **AND** data/config/output directories SHALL be mounted as volumes

#### Scenario: Container has health checks

- **WHEN** container is running
- **THEN** health check endpoint SHALL verify dependencies (OSRM, OTP2, data files)
- **AND** unhealthy container SHALL restart automatically (if orchestrated)
- **AND** health check SHALL timeout after 30 seconds

#### Scenario: Container resource limits are set

- **WHEN** deploying container
- **THEN** memory limit SHALL be set (min 16GB for full pipeline)
- **AND** CPU limit SHALL be appropriate for workload
- **AND** temp storage SHALL be at least 100GB

---

### Requirement: Data Acquisition Pipeline

The system SHALL automate acquisition of all required external data sources.

#### Scenario: Overture data is downloaded

- **WHEN** refreshing data
- **THEN** Overture Places and Transportation SHALL be downloaded for CO/UT/ID bounding boxes
- **AND** data SHALL be verified with checksums
- **AND** download SHALL be automated (script or CLI command)
- **AND** data version SHALL be recorded in manifest

#### Scenario: GTFS feeds are collected

- **WHEN** refreshing transit data
- **THEN** Transitland API SHALL be queried for CO/UT/ID agencies
- **AND** all GTFS feeds SHALL be downloaded
- **AND** feeds SHALL be validated with gtfs-kit
- **AND** invalid feeds SHALL be reported but not block pipeline

#### Scenario: Static datasets are downloaded

- **WHEN** initializing system
- **THEN** NOAA Climate Normals, PAD-US, LODES, NCES, IPEDS, FAA data SHALL be downloaded
- **AND** download scripts SHALL be idempotent (skip if already present)
- **AND** data provenance SHALL be documented
- **AND** licensing SHALL be verified for each source

#### Scenario: Data freshness is monitored

- **WHEN** running pipeline
- **THEN** data age SHALL be checked (warn if >90 days old)
- **AND** data refresh schedule SHALL be documented
- **AND** alerts SHALL fire if data is stale

---

### Requirement: Parameter Configuration Management

The system SHALL provide validated parameter configuration.

#### Scenario: Parameter YAML is validated on load

- **WHEN** loading config/params.yaml
- **THEN** Pydantic SHALL validate all 600+ parameters
- **AND** validation errors SHALL be clear and actionable
- **AND** parameter hash SHALL be computed and logged

#### Scenario: Parameter defaults are documented

- **WHEN** parameters are missing from YAML
- **THEN** application SHALL use documented defaults
- **AND** default usage SHALL be logged
- **AND** critical parameters SHALL require explicit values (no defaults)

#### Scenario: Parameter changes are tracked

- **WHEN** parameters change
- **THEN** git SHALL track changes to params.yaml
- **AND** parameter hash SHALL change
- **AND** runs with different hashes SHALL NOT be compared directly

#### Scenario: Parameter overrides are supported

- **WHEN** running experiments
- **THEN** CLI flags SHALL override YAML parameters
- **AND** overrides SHALL be logged
- **AND** final effective parameters SHALL be saved with outputs

---

### Requirement: Deployment Automation

The system SHALL support automated deployment and updates.

#### Scenario: Deployment is reproducible

- **WHEN** deploying application
- **THEN** deployment SHALL follow documented checklist
- **AND** dependencies SHALL be pinned (no surprise upgrades)
- **AND** deployment SHALL be testable in staging first

#### Scenario: Routing graph updates are automated

- **WHEN** Overture or GTFS data is updated
- **THEN** OSRM/OTP2 graphs SHALL be rebuilt automatically
- **AND** graph quality SHALL be validated before replacement
- **AND** rollback SHALL be possible if validation fails

#### Scenario: CI/CD pipeline is configured

- **WHEN** code is merged to main
- **THEN** tests SHALL run automatically
- **AND** container SHALL be built and tagged
- **AND** deployment to staging SHALL be automatic (if tests pass)
- **AND** deployment to production SHALL require approval

#### Scenario: Rollback procedure exists

- **WHEN** deployment fails or causes issues
- **THEN** previous version SHALL be restorable within 15 minutes
- **AND** rollback procedure SHALL be documented
- **AND** rollback SHALL restore code, config, and routing graphs
