# Caching Specification

## ADDED Requirements

### Requirement: Multi-Tier Cache Architecture

The system SHALL implement intelligent caching for all external data sources and API responses.

#### Scenario: Three-tier cache

- **WHEN** data is requested
- **THEN** system SHALL check caches in order:
  1. In-memory cache (LRU, 1GB max)
  2. Disk cache (DiskCache or Redis, 50GB max)
  3. External source (API call if cache miss)
- **AND** retrieved data SHALL be stored in all cache tiers

#### Scenario: Cache key schema

- **WHEN** storing cached data
- **THEN** cache key SHALL follow format: `{source}:{entity_type}:{entity_id}:{param_hash}`
- **AND** keys SHALL be unique per data source and entity
- **AND** parameter hash SHALL detect changes in query parameters

#### Scenario: TTL configuration

- **WHEN** caching data
- **THEN** Time-To-Live SHALL be set per source:
  - Wikipedia pageviews: 24 hours
  - Wikidata entities: 7 days
  - NOAA climate: 30 days
  - FAA airports: 90 days
  - Overture POIs: 90 days
  - GTFS feeds: 7 days
  - OSRM routing: 30 days
  - OTP2 routing: 7 days
- **AND** expired entries SHALL be removed automatically

---

### Requirement: API Response Caching

The system SHALL cache responses from all external APIs to improve performance and reduce costs.

#### Scenario: Wikipedia API caching

- **WHEN** fetching Wikipedia pageviews
- **THEN** response SHALL be cached with 24-hour TTL
- **AND** cache key SHALL include: article ID, date range
- **AND** cached response SHALL be returned on subsequent requests within TTL

#### Scenario: Wikidata SPARQL caching

- **WHEN** querying Wikidata
- **THEN** response SHALL be cached with 7-day TTL
- **AND** cache key SHALL include: entity QID, query hash
- **AND** SPARQL query failures SHALL NOT be cached

#### Scenario: NOAA climate data caching

- **WHEN** fetching NOAA Climate Normals
- **THEN** response SHALL be cached with 30-day TTL (data is static)
- **AND** cache key SHALL include: station ID, dataset name
- **AND** cache SHALL persist across application restarts

#### Scenario: Transitland API caching

- **WHEN** fetching GTFS feed URLs from Transitland
- **THEN** response SHALL be cached with 7-day TTL
- **AND** cache key SHALL include: agency ID, feed type (static/realtime)
- **AND** cache SHALL be invalidated on manual refresh

---

### Requirement: Routing Result Caching

The system SHALL cache travel time computations from OSRM and OTP2.

#### Scenario: OSRM routing cache

- **WHEN** querying OSRM for travel times
- **THEN** response SHALL be cached with 30-day TTL
- **AND** cache key SHALL include: profile (car/bike/foot), origin hex, destination hex, time period
- **AND** cache SHALL be invalidated when OSRM graph is rebuilt

#### Scenario: OTP2 routing cache

- **WHEN** querying OTP2 for transit itineraries
- **THEN** response SHALL be cached with 7-day TTL
- **AND** cache key SHALL include: origin, destination, modes, departure time bucket (hourly)
- **AND** cache SHALL be invalidated when OTP2 graph is rebuilt

#### Scenario: Batch routing cache

- **WHEN** computing accessibility matrices (many OD pairs)
- **THEN** individual OD pairs SHALL be cached separately
- **AND** cached results SHALL be reused across runs
- **AND** cache hit rate SHALL be logged and monitored

---

### Requirement: Cache Management UI

The system SHALL provide a user interface for viewing and managing cache status.

#### Scenario: Cache dashboard

- **WHEN** user opens "Data Management" page
- **THEN** dashboard SHALL display:
  - Total cache size (GB)
  - Cache hit rate (%)
  - Oldest cached entry (date)
  - Newest cached entry (date)
- **AND** dashboard SHALL show per-source statistics

#### Scenario: Per-source cache status

- **WHEN** viewing cache dashboard
- **THEN** for each data source (Wikipedia, Wikidata, OSRM, etc.), display:
  - Last updated timestamp
  - TTL remaining (days/hours)
  - Number of cached entries
  - Cache size (MB)
  - Hit rate (%)
- **AND** sources with stale data (>50% through TTL) SHALL be highlighted

#### Scenario: Cache refresh button

- **WHEN** user clicks "Refresh" button for a data source
- **THEN** all cache entries for that source SHALL be invalidated
- **AND** fresh data SHALL be fetched on next request
- **AND** progress indicator SHALL show fetching status
- **AND** toast notification SHALL appear on completion

#### Scenario: Refresh all caches

- **WHEN** user clicks "Refresh All" button
- **THEN** confirmation dialog SHALL appear (prevent accidental purge)
- **AND** all cache entries across all sources SHALL be invalidated
- **AND** sequential refresh SHALL be triggered (fetch fresh data)
- **AND** overall progress SHALL be displayed (X of Y sources complete)

#### Scenario: Clear cache

- **WHEN** user clicks "Clear Cache" button
- **THEN** confirmation dialog SHALL appear with warning
- **AND** all cached data SHALL be deleted
- **AND** disk space SHALL be freed
- **AND** cache statistics SHALL reset to zero

---

### Requirement: Cache Performance and Limits

The system SHALL manage cache size and performance to prevent resource exhaustion.

#### Scenario: Size limits enforced

- **WHEN** cache size approaches limit
- **THEN** LRU eviction SHALL remove least recently used entries
- **AND** eviction SHALL log: key, age, access count
- **AND** cache SHALL never exceed configured limit (50GB disk, 1GB memory)

#### Scenario: Fast cache lookups

- **WHEN** querying cache
- **THEN** lookup time SHALL be <10ms for memory cache
- **AND** lookup time SHALL be <100ms for disk cache
- **AND** cache index SHALL use efficient data structures (hash table, B-tree)

#### Scenario: Cache statistics tracking

- **WHEN** cache is accessed
- **THEN** system SHALL track:
  - Hit count (successful cache lookups)
  - Miss count (fallback to external source)
  - Eviction count (entries removed)
  - Total requests
- **AND** statistics SHALL be persisted across restarts
- **AND** statistics SHALL be queryable via API

---

### Requirement: Cache Invalidation

The system SHALL invalidate cache entries when underlying data changes.

#### Scenario: Automatic TTL expiration

- **WHEN** cached entry exceeds TTL
- **THEN** entry SHALL be marked as expired (not immediately deleted)
- **AND** next request SHALL fetch fresh data
- **AND** expired entry SHALL be replaced with fresh data

#### Scenario: Manual invalidation per source

- **WHEN** user triggers manual refresh for a data source
- **THEN** all entries for that source SHALL be invalidated
- **AND** subsequent requests SHALL fetch fresh data
- **AND** invalidation SHALL be logged

#### Scenario: Graph rebuild invalidation

- **WHEN** OSRM or OTP2 graph is rebuilt
- **THEN** all routing cache entries SHALL be invalidated
- **AND** user SHALL be notified (toast message: "Routing data updated, scores may change")
- **AND** pipeline run with new graphs SHALL not use stale routing cache

#### Scenario: Parameter change invalidation

- **WHEN** AUCS parameters change (weights, decay, VOT)
- **THEN** computed score cache SHALL be invalidated (scores will change)
- **AND** raw data cache (APIs, routing) SHALL remain valid (data unchanged)
- **AND** parameter hash SHALL be updated in run manifest

---

### Requirement: Cache Error Handling

The system SHALL handle cache errors gracefully without breaking data flow.

#### Scenario: Cache write failure

- **WHEN** writing to cache fails (disk full, permission error)
- **THEN** error SHALL be logged with full context
- **AND** data SHALL be returned to caller (cache is optimization, not requirement)
- **AND** subsequent requests SHALL attempt cache write again

#### Scenario: Cache read failure

- **WHEN** reading from cache fails (corrupted entry, deserialization error)
- **THEN** error SHALL be logged
- **AND** entry SHALL be deleted from cache
- **AND** fresh data SHALL be fetched from source

#### Scenario: Cache backend unavailable

- **WHEN** cache backend (DiskCache, Redis) is unavailable
- **THEN** system SHALL fall back to direct API calls
- **AND** warning SHALL be logged
- **AND** alert SHALL fire if unavailable >5 minutes
- **AND** UI SHALL display "Cache unavailable, performance may be degraded"

---

### Requirement: Cache Configuration

The system SHALL support configurable cache settings via YAML configuration.

#### Scenario: Cache configuration file

- **WHEN** loading cache settings
- **THEN** system SHALL read `config/cache.yaml`
- **AND** configuration SHALL include:
  - Backend type (diskcache, redis, or memory-only)
  - Size limits (memory, disk)
  - TTL per source
  - Eviction policy (LRU, LFU)
- **AND** missing configuration SHALL use sensible defaults

#### Scenario: Runtime cache tuning

- **WHEN** system is running
- **THEN** admin SHALL be able to adjust:
  - Size limits (without restart)
  - TTL per source (without restart)
  - Enable/disable caching per source (without restart)
- **AND** changes SHALL take effect immediately
- **AND** changes SHALL be persisted to config file

#### Scenario: Cache warming

- **WHEN** application starts
- **THEN** common queries SHALL be pre-populated (cache warming)
- **AND** warming SHALL happen in background (not block startup)
- **AND** warming SHALL log: entries loaded, time taken

---

### Requirement: Cache Monitoring and Alerts

The system SHALL monitor cache health and alert on issues.

#### Scenario: Cache hit rate monitoring

- **WHEN** cache is in use
- **THEN** hit rate SHALL be tracked per source
- **AND** hit rate SHALL be logged hourly
- **AND** alert SHALL fire if hit rate drops below 70% (indicates cache ineffective)

#### Scenario: Cache size monitoring

- **WHEN** cache grows
- **THEN** size SHALL be tracked (memory and disk)
- **AND** alert SHALL fire if size exceeds 90% of limit
- **AND** alert SHALL recommend increasing limit or adjusting TTLs

#### Scenario: Cache staleness monitoring

- **WHEN** cached data is old
- **THEN** system SHALL track age of oldest entry per source
- **AND** warning SHALL display in UI if data >90 days old
- **AND** users SHALL be prompted to refresh

#### Scenario: Cache performance degradation

- **WHEN** cache lookups slow down
- **THEN** system SHALL log slow queries (>100ms)
- **AND** alert SHALL fire if >10% of queries are slow
- **AND** recommendation SHALL be made (rebuild index, increase memory, etc.)
