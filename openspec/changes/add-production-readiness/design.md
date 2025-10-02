# Production Readiness Design Document

## Context

AUCS 2.0 implementation is complete with all core algorithms, data ingestion, and scoring logic in place. However, the system cannot function in production without external routing services (OSRM, OTP2), comprehensive testing, operational monitoring, and deployment automation.

**Key Challenges:**

1. **External service fragility**: OSRM and OTP2 are heavyweight services that require careful deployment, graph building, and error handling
2. **Data pipeline scale**: ~1M hexes, ~500K POIs, ~100M OD pairs requires optimization
3. **Integration complexity**: Multiple external APIs, data sources, and dependencies
4. **Operational readiness**: Need monitoring, alerting, recovery procedures for 24/7 operation

**Stakeholders:**

- Engineering team (implementation, deployment)
- Operations team (monitoring, maintenance)
- Data science team (calibration, validation)
- End users (urban planners, real estate analysts, researchers)

---

## Goals / Non-Goals

### Goals

1. **Deploy routing infrastructure**: OSRM (3 profiles) + OTP2 (1 region graph) with automated rebuild procedures
2. **Achieve test coverage**: 80%+ for core math, 60%+ for I/O, zero import errors
3. **Establish monitoring**: Structured logging, performance metrics, health checks, alerting
4. **Enable recovery**: Checkpointing, backup/restore, rollback procedures
5. **Document operations**: Runbooks, troubleshooting guides, incident response playbooks
6. **Validate quality**: End-to-end integration test, QA automation, ground truth comparison

### Non-Goals

1. **Web API**: Not building FastAPI query layer in this change (optional future work)
2. **Distributed execution**: Not implementing Spark/Dask (single-machine scale sufficient for now)
3. **Real-time updates**: Not implementing streaming pipeline (batch is sufficient)
4. **Multi-region**: CO/UT/ID only (not expanding to other states yet)
5. **Advanced visualization**: Basic maps sufficient (advanced dashboards are future work)

---

## Decisions

### Decision 1: OSRM Deployment Architecture

**What:** Deploy 3 separate OSRM instances (car, bike, foot) as Docker containers or dedicated VMs.

**Why:**

- Each profile requires separate graph built with different `*.lua` profile scripts
- Isolating profiles prevents interference and simplifies graph updates
- Docker simplifies deployment and version management

**Alternatives considered:**

- Single OSRM instance with multiple profiles: Not supported by OSRM architecture
- Build graphs on-demand: Too slow (hours per profile), not practical

**Implementation:**

- Use official OSRM Docker images: `ghcr.io/project-osrm/osrm-backend`
- Build graphs offline with `osrm-extract` + `osrm-contract`
- Mount graph directories as volumes
- Expose HTTP ports (5000, 5001, 5002 for car/bike/foot)
- Configure service discovery via environment variables

**Trade-offs:**

- Pro: Clean separation, easy to rebuild individual profiles
- Con: More resources (3x memory, ~12GB total), more containers to manage

---

### Decision 2: OTP2 Graph Scope

**What:** Build single regional OTP2 graph covering all of CO/UT/ID.

**Why:**

- OTP2 supports multi-feed graphs (can ingest 20+ GTFS feeds)
- Single graph simplifies deployment and querying
- Cross-state trip planning is possible (e.g., Denver to Salt Lake)

**Alternatives considered:**

- Separate graphs per state: More overhead, can't route cross-state
- Separate graphs per metro: Requires complex service routing, graph management

**Implementation:**

- Collect all GTFS feeds via Transitland API
- Validate feeds with `gtfs-kit`, exclude invalid ones
- Build single OTP2 graph with `--build --save`
- Deploy as single Java application (OTP 2.5+)
- Allocate 8-16GB RAM (scales with graph size)

**Trade-offs:**

- Pro: Simplest deployment, supports cross-regional queries
- Con: Large memory footprint, rebuild affects all queries
- Mitigation: Can split to metro-level graphs if performance issues arise

---

### Decision 3: Error Handling Strategy for Routing

**What:** Implement retry with exponential backoff, circuit breakers, and graceful degradation.

**Why:**

- Routing services are external and can fail (network, overload, bugs)
- Transient errors (timeouts) should be retried
- Persistent errors (no route) should fail gracefully, not crash pipeline
- Circuit breakers prevent cascading failures

**Implementation:**

- Use `tenacity` or `backoff` library for retry logic
- Retry policy: max 3 attempts, exponential backoff with jitter (1s, 2s, 4s)
- Circuit breaker: Open after 5 consecutive failures, half-open after 60s
- Fallback: Set accessibility to 0 for unreachable OD pairs, continue pipeline
- Logging: Log all failures with full context (origin, destination, mode, error)

**Monitoring:**

- Track routing success rate (should be >95%)
- Alert if success rate drops below 90%
- Dashboard showing error types and trends

**Trade-offs:**

- Pro: Resilient to transient failures, prevents pipeline crashes
- Con: Retries add latency, may hide systematic issues
- Mitigation: Monitor error rates, investigate patterns

---

### Decision 4: Testing Strategy

**What:** Three-tier testing: unit tests (mock external services) → integration tests (small real data) → pilot test (full region).

**Why:**

- Unit tests are fast and reliable (no external dependencies)
- Integration tests validate end-to-end flow on manageable data
- Pilot test validates performance and quality on production scale

**Implementation:**

**Unit Tests:**

- Mock OSRM/OTP responses with `pytest-mock` or `responses` library
- Test math kernels with property-based tests (`hypothesis`)
- Test data ingestion with synthetic data
- Test error handling with simulated failures
- Target: 80%+ coverage for core math, 60%+ for I/O

**Integration Tests:**

- Create fixture dataset: 100 hexes, 500 POIs, 2 transit routes (Boulder, CO area)
- Run full pipeline with test config (reduced parameters)
- Validate outputs: schema compliance, score ranges, reproducibility
- Use Docker Compose for local OSRM/OTP2 (test services)

**Pilot Test:**

- Select pilot region: Boulder County, CO (~5000 hexes)
- Run full pipeline with production config
- Validate quality: QA metrics, visualizations, spot-checks
- Measure performance: run time, memory, disk I/O
- Document findings and optimize

**Trade-offs:**

- Pro: Catches bugs early, validates correctness and performance
- Con: Requires test data setup, mock maintenance
- Mitigation: Invest in test fixtures, automate test data generation

---

### Decision 5: Monitoring and Observability

**What:** Implement structured logging (JSON), performance metrics, health checks, and alerting.

**Why:**

- Debugging production issues requires detailed logs
- Performance monitoring detects regressions and bottlenecks
- Health checks enable proactive issue detection
- Alerts enable rapid response to failures

**Implementation:**

**Structured Logging:**

- Use `structlog` for JSON logs
- Include: timestamp, level, logger, message, context (run_id, stage, metrics)
- Write to file (rotated, 100MB max) and stdout (container-friendly)
- Sanitize sensitive data (API keys, raw coordinates)

**Performance Metrics:**

- Timing: duration per stage, p50/p95/p99 latencies for batch ops
- Throughput: rows/sec, queries/sec
- Resources: peak memory (RSS), disk usage
- Export to logs and optionally Prometheus

**Health Checks:**

- CLI command: `aucs healthcheck` (checks OSRM, OTP2, data files, config)
- Automated on startup (fail fast if dependencies unavailable)
- Continuous monitoring: poll services every 60s during pipeline run

**Alerting:**

- Critical: Pipeline failure, service unavailability
- Warning: Data staleness, QA anomalies, performance degradation
- Delivery: Logs (parseable), email, Slack, PagerDuty (configurable)

**Trade-offs:**

- Pro: Rapid debugging, proactive issue detection, operational visibility
- Con: Logging overhead (~5% performance impact), alerting noise risk
- Mitigation: Tune log levels (INFO in prod), tune alert thresholds

---

### Decision 6: Parameter Configuration Management

**What:** Store all 600+ parameters in `config/params.yaml`, validate with Pydantic, version with git + hash.

**Why:**

- YAML is human-readable and version-controllable
- Pydantic provides schema validation and type safety
- Parameter hash enables reproducibility and change detection

**Implementation:**

- Create `config/params.yaml` from `docs/Urban_Amenities_Model_Spec.sty` reference
- Load with `config/loader.py` (Pydantic validation)
- Compute SHA256 hash of normalized parameters
- Store hash in run manifest (track which params produced outputs)
- Support CLI overrides: `aucs run --param EA.weight=32`
- Validate parameter changes with sensitivity tests

**Versioning:**

- Commit params.yaml to git (track history)
- Tag releases: `v1.0-params` when parameters frozen
- Document calibration rationale in comments

**Trade-offs:**

- Pro: Transparent, reproducible, auditable
- Con: Large file (~1000 lines), manual updates required
- Mitigation: Generate from reference spec, validate on load

---

### Decision 7: Data Acquisition and Versioning

**What:** Automate data download with scripts, track data versions in manifest, store checksums.

**Why:**

- Manual downloads are error-prone and not reproducible
- Data versions affect outputs (must track for reproducibility)
- Checksums detect corruption and incomplete downloads

**Implementation:**

**Download Scripts:**

- `scripts/download_overture.sh` (BigQuery export or S3 sync)
- `scripts/download_gtfs.py` (Transitland API + feed downloads)
- `scripts/download_static.sh` (NOAA, PAD-US, LODES, NCES, IPEDS, FAA)
- Idempotent: skip if already present (check checksums)
- Log provenance: URL, timestamp, checksum

**Data Versioning:**

- Store manifest: `data/manifest.json` (sources, versions, timestamps, checksums)
- Update manifest on data refresh
- Include manifest with outputs (enable reproducibility)

**Data Storage:**

- Raw data: `data/raw/` (as downloaded)
- Processed data: `data/processed/` (Parquet, hex-indexed, validated)
- Temp data: `data/temp/` (cleaned up after run)

**Trade-offs:**

- Pro: Reproducible, auditable, detects corruption
- Con: Disk space (raw + processed ~200GB), download time
- Mitigation: Document retention policy (delete raw after 90 days)

---

### Decision 8: Deployment Automation

**What:** Use Docker for containerization, CI/CD for testing/building, infrastructure-as-code for deployment.

**Why:**

- Docker ensures consistent environments (dev, staging, prod)
- CI/CD automates testing and catches bugs before merge
- Infrastructure-as-code (Terraform, Ansible) enables reproducible deployments

**Implementation:**

**Docker:**

- Multi-stage Dockerfile: build stage (compile dependencies) + runtime stage (minimal image)
- Base: `mambaorg/micromamba:latest` (fast conda env)
- Pin dependencies: `environment.yml` with exact versions
- Non-root user, health checks, resource limits

**CI/CD (GitHub Actions or GitLab CI):**

- On push: run linters (`ruff`, `black --check`), run tests (`pytest -q --cov`)
- On merge to main: build Docker image, tag with commit SHA
- On tag: deploy to staging, run smoke tests, promote to prod (manual approval)

**Infrastructure-as-Code:**

- Terraform: provision VMs or containers for OSRM, OTP2, application
- Ansible: configure services, deploy graphs, set up monitoring
- Document: `deployment/README.md` with step-by-step guide

**Trade-offs:**

- Pro: Reproducible, automated, reduces human error
- Con: Initial setup complexity, requires DevOps skills
- Mitigation: Start simple (manual deployment), automate incrementally

---

### Decision 9: Checkpointing and Recovery

**What:** Save intermediate outputs at each pipeline stage, enable restart from checkpoint.

**Why:**

- Full pipeline takes hours; failures should not require restarting from scratch
- Intermediate outputs are valuable for debugging
- Graceful shutdown should preserve progress

**Implementation:**

**Checkpointing:**

- Each stage saves output to `data/processed/<stage>.parquet`
- Manifest tracks completed stages: `{"data_ingest": "2025-10-02T14:30:00", ...}`
- On restart: check manifest, skip completed stages
- On clean run: delete manifest, start fresh

**Recovery:**

- On failure: preserve intermediates (do not clean up)
- Operator inspects logs, fixes issue (e.g., restart OSRM)
- Restart pipeline with `aucs run --resume`

**Cleanup:**

- On success: optionally delete intermediates (save disk space)
- Keep final outputs and manifest indefinitely

**Trade-offs:**

- Pro: Resilient to failures, saves time on retries
- Con: Disk space for intermediates (~50GB), complexity
- Mitigation: Clean up old runs, document retention policy

---

### Decision 10: QA Automation

**What:** Automatically compute QA metrics, enforce thresholds, generate reports.

**Why:**

- Manual QA is slow and inconsistent
- Automated QA catches issues before outputs are published
- Trends over time reveal regressions or data quality issues

**Implementation:**

**QA Metrics:**

- Coverage: % of hexes with non-zero scores (expect >95% in urban areas)
- Distributions: mean, median, std, min, max for each subscore
- Outliers: flag hexes with scores >3 std from mean
- Comparisons: compare with previous run (detect sudden changes)
- Spatial patterns: check urban vs rural, transit vs non-transit

**Thresholds:**

- Critical: block publication (e.g., <80% coverage, NaN values)
- Warning: log but allow (e.g., 5% increase in mean score)
- Configurable in `params.yaml` under `qa:` section

**QA Report:**

- HTML report: `output/qa_report.html` (charts, tables, summary)
- JSON metrics: `output/qa_metrics.json` (machine-readable)
- Visualization: choropleth maps, histograms, time series

**Trade-offs:**

- Pro: Catches issues early, improves confidence in outputs
- Con: Requires defining good thresholds (learned over time)
- Mitigation: Start with loose thresholds, tighten based on experience

---

## Risks / Trade-offs

### Risk 1: OSRM/OTP2 Deployment Complexity

**Risk:** Deploying and maintaining routing services requires specialized knowledge (OSM data, graph building, JVM tuning).

**Mitigation:**

- Document deployment procedures in detail (step-by-step)
- Automate graph building with scripts
- Provide pre-built Docker Compose for local testing
- Train operations team on graph rebuilds
- Consider managed services (e.g., MapBox Directions API) if internal deployment too complex

---

### Risk 2: External API Rate Limits

**Risk:** Wikipedia/Wikidata APIs may rate-limit or ban if we exceed quotas.

**Mitigation:**

- Implement aggressive caching (7-day TTL for Wikidata, 24-hour for Wikipedia)
- Respect rate limits (10 req/sec for SPARQL, 100 req/sec for Wikipedia)
- Use `User-Agent` header identifying our project and contact
- Monitor 429 errors, exponential backoff
- Fallback: skip enrichment if API unavailable (document impact on scores)

---

### Risk 3: Data Quality Variability

**Risk:** Overture data is incomplete in rural areas; GTFS feeds may have errors or become stale.

**Mitigation:**

- Validate GTFS feeds with `gtfs-kit`, exclude invalid feeds
- Document known data gaps (e.g., sparse rural POI coverage)
- Supplement with state-specific sources (USDA SNAP for rural groceries)
- Monitor data freshness, alert on stale feeds
- QA thresholds account for known gaps (lower coverage expected in rural)

---

### Risk 4: Performance Bottlenecks

**Risk:** Routing queries dominate execution time (~100M OD pairs); may exceed acceptable duration.

**Mitigation:**

- Profile to identify hotspots (cProfile, py-spy)
- Optimize batching (group nearby OD pairs, use OSRM /table efficiently)
- Implement caching (spatial index for repeated queries)
- Parallelize routing queries (async, respect rate limits)
- Consider pre-computation: build travel time skims once, reuse for multiple runs
- If still too slow: explore distributed execution (Dask, Ray) or sampling strategies

---

### Risk 5: Insufficient Test Coverage

**Risk:** Mock-heavy unit tests may not catch integration issues; pilot test may miss edge cases.

**Mitigation:**

- Balance mocks with integration tests (use test services when feasible)
- Expand pilot test to multiple regions (urban, suburban, rural)
- Use property-based tests to explore edge cases (Hypothesis)
- Monitor production for errors, add regression tests
- Continuous improvement: increase coverage with each bug fix

---

## Migration Plan

### Phase 1: External Services (Weeks 1-2)

1. Deploy OSRM services (car, bike, foot) on dev/staging environment
2. Build graphs from Overture data for CO/UT/ID
3. Deploy OTP2 service with GTFS feeds
4. Test services with sample queries, validate responses
5. Document deployment procedures and graph rebuild process

**Success Criteria:**

- OSRM /table queries return valid results (<1s latency)
- OTP2 GraphQL queries return transit itineraries (<2s latency)
- Services survive restarts and handle errors gracefully

---

### Phase 2: Testing (Weeks 2-3)

1. Fix test_cli.py import error
2. Expand unit test coverage (target 80%+ for math modules)
3. Create integration test fixtures (Boulder, CO: 100 hexes, 500 POIs)
4. Run integration test end-to-end, validate outputs
5. Set up CI/CD pipeline (run tests on every push)

**Success Criteria:**

- All tests pass (exit code 0)
- Coverage reports show targets met
- Integration test produces valid AUCS scores

---

### Phase 3: Data Pipeline (Weeks 3-4)

1. Create `config/params.yaml` from reference spec
2. Write data download scripts (Overture, GTFS, static datasets)
3. Run data ingestion, validate with Pandera schemas
4. Generate H3 grid for CO/UT/ID (~1M hexes)
5. Test checkpointing and resume functionality

**Success Criteria:**

- All data sources downloaded and validated
- H3 grid covers study area, no gaps
- Pipeline can resume from checkpoint after interruption

---

### Phase 4: Pilot Test (Weeks 4-5)

1. Run full pipeline on Boulder County, CO (~5000 hexes)
2. Validate outputs: QA metrics, visualizations, spot-checks
3. Compare with ground truth (Walk Score, AllTransit)
4. Measure performance: run time, memory, disk I/O
5. Document findings, optimize bottlenecks

**Success Criteria:**

- Pilot completes in <2 hours
- QA metrics pass thresholds
- Outputs are sensible (urban cores score high, rural scores low)

---

### Phase 5: Monitoring & Operations (Weeks 5-6)

1. Implement structured logging (JSON, rotation, sanitization)
2. Add performance metrics (timing, throughput, resources)
3. Create health check CLI command and automated checks
4. Set up alerting (critical errors, service failures)
5. Write runbooks and troubleshooting guides

**Success Criteria:**

- Logs are parseable and informative
- Metrics track key operations
- Health checks detect service failures
- Alerts fire on simulated failures

---

### Phase 6: Full Production Run (Weeks 6-7)

1. Run full pipeline on all 3 states (CO/UT/ID)
2. Monitor execution: logs, metrics, alerts
3. Validate outputs: QA report, cross-state comparisons
4. Archive outputs with manifest (params, data versions)
5. Generate QA report and share with stakeholders

**Success Criteria:**

- Full run completes in <6 hours
- QA metrics pass thresholds
- No critical errors or service failures
- Outputs ready for publication

---

### Phase 7: Deployment Automation (Weeks 7-8)

1. Create production Dockerfile and Docker Compose
2. Set up CI/CD pipeline (build, test, deploy)
3. Write infrastructure-as-code (Terraform, Ansible)
4. Test deployment in staging environment
5. Document deployment procedures and rollback

**Success Criteria:**

- Deployment is reproducible (no manual steps)
- CI/CD catches errors before merge
- Staging deployment works end-to-end

---

## Open Questions

1. **Orchestration platform**: Use Prefect, Airflow, Argo Workflows, or just cron?
   - **Decision needed by**: Week 5 (before production run)
   - **Trade-offs**: Cron is simplest but lacks retry/monitoring; Airflow is powerful but complex

2. **Query API**: Should we build FastAPI layer for querying outputs?
   - **Decision needed by**: After Phase 6 (based on user feedback)
   - **Trade-offs**: Adds value but increases scope and complexity

3. **Multi-region scaling**: How to handle future expansion to other states?
   - **Decision needed by**: After Phase 6 (assess current approach)
   - **Options**: Replicate approach per region, or build distributed system

4. **Calibration approach**: How to tune parameters (expert judgment vs data-driven)?
   - **Decision needed by**: Week 4 (pilot test)
   - **Options**: Start with expert values, refine with sensitivity analysis

5. **Output format**: Parquet only, or also GeoJSON, GeoPackage, API?
   - **Decision needed by**: After Phase 6 (based on user requests)
   - **Trade-offs**: More formats = more flexibility but more maintenance

---

## Success Metrics

**Technical Metrics:**

- Test coverage: 80%+ for core math, 60%+ for I/O
- Performance: Full 3-state run in <6 hours on 16-core machine
- Reliability: Pipeline success rate >95% over 10 runs
- Routing success rate: >95% of queries return valid results

**Operational Metrics:**

- Deployment time: <1 hour from code commit to staging deployment
- Recovery time: <15 minutes to restore from backup or rollback
- Monitoring coverage: All critical operations logged and metered

**Quality Metrics:**

- QA coverage: >95% of urban hexes have non-zero scores
- Ground truth alignment: R² >0.7 with Walk Score (sample locations)
- No critical QA violations (NaN, score >100, negative values)

---

## Timeline

**Total Duration:** 6-8 weeks with dedicated team

**Critical Path:**

1. Week 1-2: Deploy OSRM/OTP2 (blocks all testing and execution)
2. Week 2-3: Fix tests, expand coverage (blocks CI/CD)
3. Week 3-4: Data pipeline setup (blocks pilot test)
4. Week 4-5: Pilot test (validates approach, identifies issues)
5. Week 5-6: Monitoring & operations (enables production run)
6. Week 6-7: Full production run (first real outputs)
7. Week 7-8: Deployment automation (enables ongoing operations)

**Parallelization:**

- Monitoring/operations work (Phase 5) can start in parallel with pilot test (Phase 4)
- Documentation can be written throughout

**Buffer:** 2 weeks for unexpected issues, iteration, optimization
