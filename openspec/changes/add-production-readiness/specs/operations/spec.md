# Operations Specification

## ADDED Requirements

### Requirement: Structured Logging

The system SHALL provide comprehensive structured logging for production operations.

#### Scenario: All logs use JSON format

- **WHEN** running in production
- **THEN** logs SHALL be emitted as JSON (using structlog)
- **AND** each log SHALL include: timestamp, level, logger name, message, context fields
- **AND** request_id SHALL be included to trace pipeline runs

#### Scenario: Log levels are configurable

- **WHEN** configuring application
- **THEN** log level SHALL be set via environment variable (LOG_LEVEL)
- **AND** valid levels SHALL be: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **AND** production default SHALL be INFO

#### Scenario: Sensitive data is sanitized

- **WHEN** logging
- **THEN** API keys SHALL NOT appear in logs
- **AND** raw coordinates SHALL be rounded to 3 decimals (geo-privacy)
- **AND** user identifiers (if any) SHALL be hashed

#### Scenario: Logs are written to multiple destinations

- **WHEN** application is running
- **THEN** logs SHALL be written to both file and stdout
- **AND** file logs SHALL be rotated (max 100MB, keep 10 files)
- **AND** stdout logs SHALL be container-friendly (one JSON per line)

#### Scenario: Critical operations are logged

- **WHEN** pipeline executes
- **THEN** start/stop of each stage SHALL be logged
- **AND** row counts and file sizes SHALL be logged
- **AND** timing SHALL be logged for major operations
- **AND** errors SHALL be logged with full context and traceback

---

### Requirement: Performance Monitoring

The system SHALL collect and expose performance metrics.

#### Scenario: Timing metrics are collected

- **WHEN** running pipeline
- **THEN** duration SHALL be measured for: data ingest, routing queries, score computation, export
- **AND** p50, p95, p99 percentiles SHALL be computed for batch operations
- **AND** metrics SHALL be logged and optionally exported (Prometheus format)

#### Scenario: Throughput metrics are collected

- **WHEN** processing data
- **THEN** rows/second SHALL be measured for: POI processing, hex aggregation, routing queries
- **AND** throughput SHALL be compared to expected baselines
- **AND** significant slowdowns SHALL trigger warnings

#### Scenario: Resource utilization is monitored

- **WHEN** application is running
- **THEN** peak memory usage SHALL be logged (RSS)
- **AND** disk usage SHALL be monitored (temp files, output files)
- **AND** CPU utilization SHALL be logged (if available)
- **AND** out-of-resource conditions SHALL cause graceful failure with clear error

#### Scenario: External service metrics are tracked

- **WHEN** calling OSRM, OTP2, or external APIs
- **THEN** response times SHALL be logged (per request)
- **AND** success rate SHALL be tracked (ratio of successful/total requests)
- **AND** error types SHALL be categorized (timeout, 4xx, 5xx)
- **AND** dashboards SHALL visualize service health

---

### Requirement: Error Handling and Recovery

The system SHALL handle errors gracefully and support recovery.

#### Scenario: Routing errors are retried

- **WHEN** routing service call fails (timeout, connection error)
- **THEN** request SHALL be retried with exponential backoff (max 3 retries)
- **AND** backoff SHALL include jitter to avoid thundering herd
- **AND** persistent failures SHALL be logged and skipped

#### Scenario: Data validation errors are reported

- **WHEN** data fails schema validation
- **THEN** validation errors SHALL be logged with row details
- **AND** pipeline SHALL fail fast (do not continue with invalid data)
- **AND** error report SHALL include: file, row number, field, expected vs actual

#### Scenario: Partial failures are handled

- **WHEN** optional enrichment fails (Wikipedia API down)
- **THEN** pipeline SHALL continue without enrichment
- **AND** degraded mode SHALL be logged
- **AND** output SHALL flag missing enrichments

#### Scenario: Pipeline can resume from checkpoint

- **WHEN** pipeline fails mid-execution
- **THEN** completed stages SHALL be preserved (Parquet files)
- **AND** restart SHALL skip completed stages
- **AND** checkpoint state SHALL be tracked (manifest file)

#### Scenario: Resource exhaustion is detected early

- **WHEN** starting pipeline
- **THEN** available disk space SHALL be checked (require min 100GB free)
- **AND** available memory SHALL be checked (require min 8GB)
- **AND** insufficient resources SHALL cause pre-flight failure with clear message

---

### Requirement: Health Checks

The system SHALL provide health check mechanisms for dependencies.

#### Scenario: Application health check CLI

- **WHEN** running `aucs healthcheck`
- **THEN** OSRM services SHALL be tested (all 3 profiles)
- **AND** OTP2 service SHALL be tested
- **AND** required data files SHALL be checked (existence, recency)
- **AND** parameter file SHALL be validated
- **AND** report SHALL indicate: ✅ OK, ⚠️ Warning, ❌ Critical

#### Scenario: Service health checks are automated

- **WHEN** application initializes
- **THEN** routing services SHALL be pinged (5 sec timeout)
- **AND** failed health checks SHALL prevent application start
- **AND** health check results SHALL be logged

#### Scenario: Data freshness is checked

- **WHEN** running pipeline
- **THEN** Overture data age SHALL be checked (warn if >90 days)
- **AND** GTFS feed age SHALL be checked (warn if >7 days)
- **AND** stale data SHALL NOT block run but SHALL be logged

#### Scenario: Continuous health monitoring

- **WHEN** pipeline is running
- **THEN** service health SHALL be checked periodically (every 60 seconds)
- **AND** service degradation SHALL trigger circuit breaker
- **AND** recovery SHALL be detected and logged

---

### Requirement: Alerting and Notifications

The system SHALL provide alerting for operational issues.

#### Scenario: Critical errors trigger alerts

- **WHEN** pipeline fails with critical error
- **THEN** alert SHALL be sent (email, Slack, PagerDuty, or logs)
- **AND** alert SHALL include: error message, traceback, timestamp, run_id
- **AND** alert SHALL be actionable (suggest next steps)

#### Scenario: Service degradation triggers alerts

- **WHEN** external service failure rate exceeds 10%
- **THEN** alert SHALL be sent with service name and failure details
- **AND** alert SHALL include recent error samples

#### Scenario: Data quality issues trigger alerts

- **WHEN** output QA checks fail
- **THEN** alert SHALL include: metric name, expected vs actual, timestamp
- **AND** pipeline SHALL NOT publish outputs if QA critical

#### Scenario: Long-running operations trigger notifications

- **WHEN** pipeline stage exceeds expected duration by 50%
- **THEN** notification SHALL be sent (not critical alert)
- **AND** notification SHALL include: stage name, expected vs actual duration

---

### Requirement: Backup and Recovery

The system SHALL support data backup and disaster recovery.

#### Scenario: Critical data is backed up

- **WHEN** pipeline completes
- **THEN** final outputs SHALL be copied to backup location
- **AND** parameter file and manifest SHALL be included
- **AND** backup SHALL be versioned (timestamped)

#### Scenario: Routing graphs are backed up

- **WHEN** OSRM/OTP2 graphs are rebuilt
- **THEN** previous graphs SHALL be archived before replacement
- **AND** archives SHALL be retained for 3 months
- **AND** restoration procedure SHALL be documented

#### Scenario: Backup restoration is tested

- **WHEN** testing disaster recovery
- **THEN** outputs SHALL be restorable from backup within 1 hour
- **AND** restoration SHALL be tested quarterly
- **AND** restoration procedure SHALL be documented

#### Scenario: Interim outputs are preserved

- **WHEN** pipeline executes
- **THEN** intermediate Parquet files SHALL be retained for 30 days
- **AND** temp files SHALL be cleaned up after successful run
- **AND** failed runs SHALL preserve intermediates for debugging

---

### Requirement: Orchestration and Scheduling

The system SHALL support automated execution and scheduling.

#### Scenario: Pipeline is orchestrated

- **WHEN** using orchestrator (Prefect, Airflow, or cron)
- **THEN** task dependencies SHALL be explicit (DAG)
- **AND** tasks SHALL have timeouts (prevent hung tasks)
- **AND** task retries SHALL be configured (max 2 retries)

#### Scenario: Schedule is configurable

- **WHEN** configuring pipeline schedule
- **THEN** execution frequency SHALL be configurable (weekly, monthly, on-demand)
- **AND** execution SHALL respect maintenance windows
- **AND** manual triggers SHALL be supported

#### Scenario: Concurrent runs are prevented

- **WHEN** scheduling pipeline
- **THEN** only one run SHALL execute at a time (mutex)
- **AND** overlapping runs SHALL be rejected with clear message
- **AND** run locks SHALL be cleaned up after completion

#### Scenario: Execution history is tracked

- **WHEN** pipeline executes
- **THEN** run metadata SHALL be recorded: start time, end time, status, outputs
- **AND** history SHALL be queryable (last 100 runs)
- **AND** failed runs SHALL be marked for investigation

---

### Requirement: Documentation and Runbooks

The system SHALL provide comprehensive operational documentation.

#### Scenario: Runbook for common operations

- **WHEN** operators need to perform routine tasks
- **THEN** runbook SHALL document: start/stop pipeline, update data, rebuild graphs
- **AND** runbook SHALL include commands and expected outputs
- **AND** runbook SHALL be tested quarterly

#### Scenario: Troubleshooting guide

- **WHEN** errors occur
- **THEN** troubleshooting guide SHALL list common errors and solutions
- **AND** guide SHALL include: error message patterns, root causes, remediation steps
- **AND** guide SHALL be updated when new errors are encountered

#### Scenario: Incident response playbook

- **WHEN** major incident occurs (prolonged outage, data loss)
- **THEN** playbook SHALL define: roles, communication, escalation, resolution steps
- **AND** playbook SHALL include contact list and on-call rotation
- **AND** playbook SHALL be tested with table-top exercises

#### Scenario: Architecture documentation

- **WHEN** onboarding new operators
- **THEN** architecture diagram SHALL show: components, data flows, dependencies
- **AND** documentation SHALL explain: how OSRM/OTP2 work, data sources, parameter tuning
- **AND** documentation SHALL be versioned with code

---

### Requirement: Data Quality Assurance

The system SHALL automatically validate output quality.

#### Scenario: QA metrics are computed

- **WHEN** pipeline completes
- **THEN** QA report SHALL include: hex coverage (% with scores), score distributions, outlier detection
- **AND** QA SHALL compare with previous run (detect sudden changes)

#### Scenario: QA thresholds are enforced

- **WHEN** QA metrics are computed
- **THEN** critical violations SHALL block output publication
- **AND** warnings SHALL be logged but allow publication
- **AND** thresholds SHALL be configurable (params.yaml)

#### Scenario: Spatial patterns are validated

- **WHEN** validating outputs
- **THEN** urban cores SHALL score higher than rural areas (sanity check)
- **AND** hexes near transit SHALL have higher MORR subscore
- **AND** unexpected patterns SHALL be flagged for investigation

#### Scenario: Mathematical properties are checked

- **WHEN** validating outputs
- **THEN** all scores SHALL be in [0, 100]
- **AND** subscore weights SHALL sum to 100
- **AND** accessibility SHALL be non-negative
- **AND** no NaN or Inf values SHALL exist

---

### Requirement: Performance Profiling

The system SHALL support performance analysis and optimization.

#### Scenario: Profiling is enabled on demand

- **WHEN** investigating performance issues
- **THEN** cProfile or py-spy SHALL be usable
- **AND** profiling SHALL identify hotspots (CPU-bound functions)
- **AND** profiling overhead SHALL be acceptable (<10% slowdown)

#### Scenario: Memory profiling is available

- **WHEN** investigating memory issues
- **THEN** memory_profiler SHALL be usable
- **AND** memory usage SHALL be tracked per function
- **AND** memory leaks SHALL be detectable

#### Scenario: Performance baselines are documented

- **WHEN** measuring performance
- **THEN** expected run time for full 3-state SHALL be documented
- **AND** expected throughput (hexes/sec, queries/sec) SHALL be documented
- **AND** significant deviations SHALL trigger investigation

#### Scenario: Bottlenecks are identified

- **WHEN** profiling reveals bottleneck
- **THEN** optimization opportunities SHALL be documented
- **AND** trade-offs SHALL be evaluated (speed vs accuracy vs complexity)
- **AND** optimizations SHALL be tested for correctness
