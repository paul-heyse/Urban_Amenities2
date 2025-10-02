# Production Readiness Implementation Tasks

## 1. External Service Integration (CRITICAL)

### 1.1 OSRM Deployment

- [ ] 1.1.1 Download Overture Transportation segments for CO/UT/ID from S3 or BigQuery
- [ ] 1.1.2 Convert Overture segments to OSM-compatible format (using `osmium` or custom script)
- [ ] 1.1.3 Build OSRM car profile: `osrm-extract -p car.lua merged.osm.pbf && osrm-contract merged.osrm`
- [ ] 1.1.4 Build OSRM bike profile: `osrm-extract -p bike.lua merged.osm.pbf && osrm-contract merged.osrm`
- [ ] 1.1.5 Build OSRM foot profile: `osrm-extract -p foot.lua merged.osm.pbf && osrm-contract merged.osrm`
- [ ] 1.1.6 Deploy OSRM backend services (3 instances, one per profile) using Docker or dedicated servers
- [ ] 1.1.7 Configure OSRM service URLs in application config (env vars or secrets manager)
- [ ] 1.1.8 Validate OSRM services with test queries (sample OD pairs from each state)
- [ ] 1.1.9 Implement health checks for OSRM endpoints (retry logic, circuit breakers)
- [ ] 1.1.10 Document OSRM graph rebuild procedure and schedule (quarterly with Overture updates)

### 1.2 OpenTripPlanner 2 Deployment

- [ ] 1.2.1 Download GTFS feeds for all 20+ agencies in CO/UT/ID using Transitland registry
- [ ] 1.2.2 Validate GTFS feeds with `gtfs-kit` (check for errors, missing stops, invalid dates)
- [ ] 1.2.3 Prepare Overture street network in OTP-compatible format (GeoJSON or OSM PBF)
- [ ] 1.2.4 Build OTP2 graph: `java -Xmx8G -jar otp-shaded.jar --build --save /var/otp/graphs/region`
- [ ] 1.2.5 Deploy OTP2 GraphQL service (JVM with 8-16GB RAM per region)
- [ ] 1.2.6 Configure OTP2 service URL in application config (env vars)
- [ ] 1.2.7 Validate OTP2 with test transit queries (known routes in Denver, Salt Lake, Boise)
- [ ] 1.2.8 Implement health checks and GraphQL error handling (timeout, retry, fallback)
- [ ] 1.2.9 Document OTP2 graph rebuild procedure (weekly or as GTFS feeds update)
- [ ] 1.2.10 Set up GTFS feed monitoring (detect feed updates, trigger graph rebuilds)

### 1.3 External API Integrations

- [ ] 1.3.1 Register for Transitland API key (v2 REST API)
- [ ] 1.3.2 Store API keys in secrets manager (AWS Secrets Manager, HashiCorp Vault, or .env for dev)
- [ ] 1.3.3 Implement rate limiting for Wikipedia pageviews API (100 req/sec max)
- [ ] 1.3.4 Implement rate limiting for Wikidata SPARQL endpoint (be respectful, ~10 req/sec)
- [ ] 1.3.5 Add exponential backoff with jitter for all external API calls
- [ ] 1.3.6 Implement circuit breaker pattern for API failures (use `tenacity` or `backoff`)
- [ ] 1.3.7 Cache API responses with TTL (use `diskcache` or Redis)
- [ ] 1.3.8 Document API quota limits and monitoring thresholds
- [ ] 1.3.9 Set up alerting for API rate limit exhaustion
- [ ] 1.3.10 Test API error handling (simulate 429, 503, timeout responses)

## 2. Data Pipeline Configuration (CRITICAL)

### 2.1 Parameter Configuration

- [ ] 2.1.1 Create `config/params.yaml` from `docs/Urban_Amenities_Model_Spec.sty` reference YAML
- [ ] 2.1.2 Validate all 600+ parameters with Pydantic: `python -m Urban_Amenities2.config.loader config/params.yaml`
- [ ] 2.1.3 Generate parameter hash and store in version manifest
- [ ] 2.1.4 Document parameter tuning process (calibration methodology)
- [ ] 2.1.5 Create parameter sensitivity test suite (vary key parameters, check output stability)
- [ ] 2.1.6 Set up parameter versioning (git tag on changes, track hash in outputs)
- [ ] 2.1.7 Implement parameter override mechanism for experiments (CLI flags, env vars)
- [ ] 2.1.8 Document all parameter units, ranges, and dependencies
- [ ] 2.1.9 Create parameter validation schema with Pandera (bounds checks)
- [ ] 2.1.10 Test parameter loading errors and validation failures

### 2.2 Data Acquisition

- [ ] 2.2.1 Document Overture Maps download procedure (BigQuery export or S3/Azure sync)
- [ ] 2.2.2 Write script to download Overture Places for CO/UT/ID bounding boxes
- [ ] 2.2.3 Write script to download Overture Transportation for CO/UT/ID
- [ ] 2.2.4 Download NOAA Climate Normals for all weather stations in study area
- [ ] 2.2.5 Download PAD-US protected areas shapefile (state subset)
- [ ] 2.2.6 Download LODES v8 jobs data for CO/UT/ID (OD, WAC, RAC files)
- [ ] 2.2.7 Download NCES public schools data (filtered to CO/UT/ID)
- [ ] 2.2.8 Download IPEDS universities data (filtered to study area)
- [ ] 2.2.9 Download FAA airport enplanement data (2023 or latest)
- [ ] 2.2.10 Verify data checksums and integrity (file sizes, row counts)
- [ ] 2.2.11 Document data provenance and licensing for all sources
- [ ] 2.2.12 Set up data refresh schedule and monitoring (quarterly for static sources)

### 2.3 H3 Grid Generation

- [ ] 2.3.1 Define study area bounding boxes for CO/UT/ID (WGS84 coordinates)
- [ ] 2.3.2 Generate H3 resolution 9 hex grid covering study area (~1M hexes)
- [ ] 2.3.3 Filter hexes to land areas only (exclude water bodies, extreme elevations)
- [ ] 2.3.4 Compute hex centroids for routing (lat/lon for each hex)
- [ ] 2.3.5 Identify metro areas and assign metro tags (Denver, SLC, Boise, etc.)
- [ ] 2.3.6 Export hex grid to Parquet with schema validation
- [ ] 2.3.7 Create hex neighbor lookup table (1-ring neighbors for spatial operations)
- [ ] 2.3.8 Document hex grid versioning (track if resolution changes)
- [ ] 2.3.9 Validate hex grid coverage (no gaps, no duplicate hexes)
- [ ] 2.3.10 Create visualization of hex grid for QA (folium map)

## 3. End-to-End Integration Testing (CRITICAL)

### 3.1 Unit Test Fixes

- [ ] 3.1.1 Fix `test_cli.py` import error (investigate missing dependencies)
- [ ] 3.1.2 Run full test suite: `pytest -q --tb=short`
- [ ] 3.1.3 Achieve 80%+ coverage for core math modules (`pytest --cov=src/Urban_Amenities2/math`)
- [ ] 3.1.4 Achieve 60%+ coverage for I/O modules (`pytest --cov=src/Urban_Amenities2/io`)
- [ ] 3.1.5 Add property-based tests with Hypothesis for mathematical invariants
- [ ] 3.1.6 Test edge cases (zero accessibility, missing POIs, unreachable hexes)
- [ ] 3.1.7 Mock external services in unit tests (OSRM, OTP, APIs)
- [ ] 3.1.8 Test error handling (routing failures, API timeouts, invalid GTFS)
- [ ] 3.1.9 Run tests in CI/CD pipeline (GitHub Actions, GitLab CI)
- [ ] 3.1.10 Generate test coverage report and upload to Codecov or similar

### 3.2 Integration Testing

- [ ] 3.2.1 Create small test dataset (100 hexes, 500 POIs, 2 transit routes)
- [ ] 3.2.2 Run full pipeline on test dataset: `aucs run --config test_config.yaml`
- [ ] 3.2.3 Validate schema compliance at each stage (ingest → compute → export)
- [ ] 3.2.4 Check output AUCS scores are in valid range (0-100)
- [ ] 3.2.5 Verify mathematical properties (monotonicity, homogeneity)
- [ ] 3.2.6 Compare results with hand-calculated examples (5-10 hexes)
- [ ] 3.2.7 Test reproducibility (same inputs + params → same outputs)
- [ ] 3.2.8 Test parameter sensitivity (vary key params, check reasonable changes)
- [ ] 3.2.9 Validate explainability output (top contributors are sensible)
- [ ] 3.2.10 Document expected run time for full state (extrapolate from test)

### 3.3 Full-Scale Pilot Test

- [ ] 3.3.1 Select pilot region (e.g., Boulder County, CO - manageable size)
- [ ] 3.3.2 Run full pipeline on pilot region with production parameters
- [ ] 3.3.3 Validate routing services handle expected query volume
- [ ] 3.3.4 Monitor memory usage and disk I/O (ensure no OOM, reasonable temp space)
- [ ] 3.3.5 Validate output quality (spot-check high/low scoring hexes)
- [ ] 3.3.6 Create visualizations (choropleth maps, distribution histograms)
- [ ] 3.3.7 Compare with known ground truth (walkability scores, transit access)
- [ ] 3.3.8 Document any unexpected results or anomalies
- [ ] 3.3.9 Measure actual vs expected run time (identify bottlenecks)
- [ ] 3.3.10 Generate QA report with summary statistics and visuals

## 4. Monitoring and Observability (HIGH PRIORITY)

### 4.1 Structured Logging

- [x] 4.1.1 Configure structlog for JSON logging in production
- [x] 4.1.2 Set log level via environment variable (INFO for prod, DEBUG for dev)
- [x] 4.1.3 Add request IDs to all log entries (track pipeline runs)
- [x] 4.1.4 Log timing for all major operations (ingest, routing, scoring)
- [x] 4.1.5 Log data volumes (row counts, file sizes) at each stage
- [x] 4.1.6 Sanitize sensitive data from logs (no API keys, no raw coordinates)
- [x] 4.1.7 Implement log rotation (max size, retention period)
- [x] 4.1.8 Write logs to both file and stdout (container-friendly)
- [x] 4.1.9 Test log parsing with jq or similar (validate JSON structure)
- [x] 4.1.10 Document log schema and standard fields

### 4.2 Metrics and Monitoring

- [x] 4.2.1 Instrument code with timing metrics (use `time.perf_counter()`)
- [x] 4.2.2 Track rows processed per second for batch operations
- [x] 4.2.3 Monitor OSRM/OTP response times (p50, p95, p99 latencies)
- [x] 4.2.4 Monitor API call success rates and retries
- [ ] 4.2.5 Track disk usage (temp files, output files)
- [ ] 4.2.6 Track memory usage (RSS, peak memory per stage)
- [ ] 4.2.7 Export metrics to Prometheus or similar (if using orchestration)
- [ ] 4.2.8 Create Grafana dashboard for pipeline monitoring (if applicable)
- [ ] 4.2.9 Set up alerting for anomalies (long run times, high error rates)
- [x] 4.2.10 Document expected metrics and thresholds for alerting

### 4.3 Health Checks

- [x] 4.3.1 Implement health check endpoint for OSRM services
- [x] 4.3.2 Implement health check endpoint for OTP2 service
- [x] 4.3.3 Implement dependency checker CLI command: `aucs healthcheck`
- [x] 4.3.4 Check parameter file validity on startup
- [x] 4.3.5 Check data file existence and recency (warn if stale)
- [x] 4.3.6 Check disk space before starting pipeline (require min 100GB free)
- [x] 4.3.7 Test database/service connectivity before processing
- [ ] 4.3.8 Implement graceful degradation (skip optional enrichments if API down)
- [x] 4.3.9 Document startup checklist (what to verify before running)
- [ ] 4.3.10 Create automated pre-flight check script

## 5. Performance Optimization (MEDIUM PRIORITY)

### 5.1 Routing Optimization

- [ ] 5.1.1 Profile routing call patterns (identify most expensive queries)
- [ ] 5.1.2 Implement intelligent batching (group nearby OD pairs)
- [ ] 5.1.3 Cache routing results with spatial indexing (rtree or PostGIS)
- [ ] 5.1.4 Implement parallel routing queries (async with httpx or concurrent.futures)
- [ ] 5.1.5 Set aggressive timeouts for routing (30s max, fail fast)
- [ ] 5.1.6 Implement distance-based pre-filtering (skip routing for >60min expected)
- [ ] 5.1.7 Use OSRM /table endpoint efficiently (max batch size 100×100)
- [ ] 5.1.8 Profile OTP2 GraphQL query performance (optimize query complexity)
- [ ] 5.1.9 Monitor routing service CPU/memory (scale horizontally if needed)
- [ ] 5.1.10 Document routing performance characteristics (queries/sec, avg latency)

### 5.2 Data Processing Optimization

- [ ] 5.2.1 Profile data pipeline with cProfile or py-spy (find hotspots)
- [ ] 5.2.2 Use Polars or DuckDB for large aggregations (faster than pandas)
- [ ] 5.2.3 Optimize Parquet file sizes (row groups, compression, partitioning)
- [ ] 5.2.4 Implement chunked processing for large datasets (avoid loading all in RAM)
- [ ] 5.2.5 Use Numba JIT for tight loops in math kernels
- [ ] 5.2.6 Vectorize operations where possible (numpy, pandas)
- [ ] 5.2.7 Minimize data copies (use views, inplace operations)
- [ ] 5.2.8 Profile memory usage with memory_profiler (find leaks)
- [ ] 5.2.9 Implement progress bars for long-running operations (tqdm)
- [ ] 5.2.10 Document expected run time for full 3-state processing

### 5.3 Parallel Execution

- [ ] 5.3.1 Identify parallelizable stages (state-level, metro-level parallelism)
- [ ] 5.3.2 Implement parallel processing with Dask or Ray (if needed)
- [ ] 5.3.3 Use joblib for embarrassingly parallel tasks (POI scoring, hex aggregation)
- [ ] 5.3.4 Configure worker pool sizes based on available cores
- [ ] 5.3.5 Handle task failures gracefully (retry, skip, log)
- [ ] 5.3.6 Monitor worker utilization (ensure no idle workers)
- [ ] 5.3.7 Avoid over-parallelization (respect OSRM/OTP rate limits)
- [ ] 5.3.8 Test on multi-core machine (8-16 cores)
- [ ] 5.3.9 Document speedup achieved from parallelization
- [ ] 5.3.10 Profile memory usage under parallel execution (avoid OOM)

## 6. Error Handling and Resilience (HIGH PRIORITY)

### 6.1 Routing Failure Handling

- [ ] 6.1.1 Implement retry with exponential backoff for routing requests (max 3 retries)
- [ ] 6.1.2 Handle OSRM "No route found" gracefully (set accessibility to 0)
- [ ] 6.1.3 Handle OTP2 GraphQL errors (missing transit, invalid coordinates)
- [ ] 6.1.4 Set hard timeout for routing queries (30s max)
- [ ] 6.1.5 Implement fallback modes (if transit fails, use car/walk only)
- [ ] 6.1.6 Log all routing failures with context (origin, destination, mode)
- [ ] 6.1.7 Track routing failure rate (alert if >10% of queries fail)
- [ ] 6.1.8 Validate routing responses (check for NaN, negative times)
- [ ] 6.1.9 Test routing services under failure conditions (stop services mid-run)
- [ ] 6.1.10 Document expected failure rate and handling strategy

### 6.2 Data Validation and Recovery

- [ ] 6.2.1 Validate Overture data schema on ingest (Pandera checks)
- [ ] 6.2.2 Validate GTFS feeds with gtfs-kit (reject invalid feeds)
- [ ] 6.2.3 Handle missing POI attributes (use defaults, flag for review)
- [ ] 6.2.4 Handle missing climate data (use regional averages)
- [ ] 6.2.5 Detect and report data anomalies (sudden drops in POI counts)
- [ ] 6.2.6 Implement checkpointing (save intermediate results, resume from failure)
- [ ] 6.2.7 Validate output schemas at each stage (fail fast on violations)
- [ ] 6.2.8 Implement data quality checks (min hex count, score distributions)
- [ ] 6.2.9 Log data quality metrics (coverage, completeness)
- [ ] 6.2.10 Test recovery from partial pipeline failure (resume from checkpoint)

### 6.3 API Failure Handling

- [ ] 6.3.1 Implement circuit breaker for Wikipedia API (open after 5 failures)
- [ ] 6.3.2 Implement circuit breaker for Wikidata SPARQL (open after 5 failures)
- [ ] 6.3.3 Handle rate limit errors (429) with exponential backoff
- [ ] 6.3.4 Handle API downtime gracefully (skip enrichment, use defaults)
- [ ] 6.3.5 Implement stale cache fallback (use cached data if API unavailable)
- [ ] 6.3.6 Log all API failures with full context (URL, status code, response)
- [ ] 6.3.7 Track API success rate per endpoint (monitor trends)
- [ ] 6.3.8 Test API error scenarios (mock 429, 503, timeout)
- [ ] 6.3.9 Document impact of enrichment failures on AUCS scores
- [ ] 6.3.10 Implement notification for prolonged API outages

## 7. Deployment and Operations (HIGH PRIORITY)

### 7.1 Container Configuration

- [ ] 7.1.1 Create production Dockerfile (multi-stage build, optimized layers)
- [ ] 7.1.2 Pin all dependencies to specific versions (requirements.txt or environment.yml)
- [ ] 7.1.3 Use micromamba in container for fast environment setup
- [ ] 7.1.4 Set up non-root user in container (security best practice)
- [ ] 7.1.5 Configure container health check (HEALTHCHECK in Dockerfile)
- [ ] 7.1.6 Set container resource limits (memory, CPU)
- [ ] 7.1.7 Mount volumes for data, config, and outputs
- [ ] 7.1.8 Pass configuration via environment variables (12-factor app)
- [ ] 7.1.9 Test container locally (docker-compose with OSRM/OTP services)
- [ ] 7.1.10 Document container build and run procedures

### 7.2 Orchestration Setup

- [ ] 7.2.1 Choose orchestration tool (Airflow, Prefect, Argo Workflows, or cron)
- [ ] 7.2.2 Define pipeline DAG (task dependencies, parallelism)
- [ ] 7.2.3 Implement task retry logic (max retries, backoff strategy)
- [ ] 7.2.4 Set up task timeout policies (prevent hung tasks)
- [ ] 7.2.5 Configure notifications (email, Slack) for failures
- [ ] 7.2.6 Implement manual approval gates (before large operations)
- [ ] 7.2.7 Set up scheduling (weekly, monthly, or on-demand)
- [ ] 7.2.8 Monitor orchestrator health (uptime, task queue depth)
- [ ] 7.2.9 Document pipeline execution procedures (start, stop, restart)
- [ ] 7.2.10 Test full pipeline in orchestration environment

### 7.3 Deployment Automation

- [ ] 7.3.1 Create deployment checklist (pre-flight, execution, post-flight)
- [ ] 7.3.2 Implement blue-green or canary deployment strategy (if web service)
- [ ] 7.3.3 Set up CI/CD pipeline (test, build, deploy on merge to main)
- [ ] 7.3.4 Automate routing engine graph updates (trigger on data refresh)
- [ ] 7.3.5 Implement rollback procedure (restore previous outputs, config)
- [ ] 7.3.6 Document deployment dependencies (services, data, credentials)
- [ ] 7.3.7 Create smoke tests for post-deployment validation
- [ ] 7.3.8 Set up deployment notifications (start, success, failure)
- [ ] 7.3.9 Maintain deployment log (version, timestamp, operator, outcome)
- [ ] 7.3.10 Test deployment procedure in staging environment

## 8. Security and Compliance (MEDIUM PRIORITY)

### 8.1 Secrets Management

- [ ] 8.1.1 Use secrets manager for API keys (AWS Secrets Manager, Vault, or .env with gitignore)
- [ ] 8.1.2 Never commit secrets to git (audit history, rotate if found)
- [ ] 8.1.3 Use environment variables for database connection strings
- [ ] 8.1.4 Encrypt sensitive configuration files at rest
- [ ] 8.1.5 Implement least-privilege access (role-based access control)
- [ ] 8.1.6 Rotate API keys and credentials periodically (quarterly)
- [ ] 8.1.7 Document credential rotation procedure
- [ ] 8.1.8 Audit access logs for secrets manager (detect unauthorized access)
- [ ] 8.1.9 Test secret rotation without service interruption
- [ ] 8.1.10 Create incident response plan for credential leaks

### 8.2 Data Privacy

- [ ] 8.2.1 Verify all outputs are aggregated to 250m hex (no PII)
- [ ] 8.2.2 Document data provenance and licensing for all inputs
- [ ] 8.2.3 Implement data retention policy (delete temp files after 30 days)
- [ ] 8.2.4 Anonymize logs (remove coordinates, specific addresses)
- [ ] 8.2.5 Review data sharing agreements (ensure compliance)
- [ ] 8.2.6 Implement data access controls (who can view/export outputs)
- [ ] 8.2.7 Document data processing agreements (GDPR-like requirements)
- [ ] 8.2.8 Audit data flows (input sources → processing → outputs)
- [ ] 8.2.9 Test data deletion procedures (right to erasure)
- [ ] 8.2.10 Create privacy policy for data products

### 8.3 Vulnerability Management

- [ ] 8.3.1 Scan dependencies for known vulnerabilities (safety, pip-audit)
- [ ] 8.3.2 Set up automated dependency updates (Dependabot, Renovate)
- [ ] 8.3.3 Pin dependency versions (avoid surprise breaking changes)
- [ ] 8.3.4 Test updates in staging before production
- [ ] 8.3.5 Monitor security advisories for key dependencies
- [ ] 8.3.6 Implement Web Application Firewall (if exposing API)
- [ ] 8.3.7 Use HTTPS/TLS for all external communications
- [ ] 8.3.8 Implement input validation (prevent injection attacks)
- [ ] 8.3.9 Document security update procedures
- [ ] 8.3.10 Conduct security review before production launch

## 9. Documentation and Training (MEDIUM PRIORITY)

### 9.1 Operational Documentation

- [ ] 9.1.1 Create runbook for common operations (start, stop, restart pipeline)
- [ ] 9.1.2 Document troubleshooting procedures (common errors and fixes)
- [ ] 9.1.3 Create architecture diagram (components, data flows, dependencies)
- [ ] 9.1.4 Document all configuration options (params.yaml reference)
- [ ] 9.1.5 Create API documentation for routing services (if custom wrappers)
- [ ] 9.1.6 Document data refresh procedures (how to update sources)
- [ ] 9.1.7 Create incident response playbook (outage, data quality, performance)
- [ ] 9.1.8 Document backup and recovery procedures
- [ ] 9.1.9 Create FAQ for common questions (parameter tuning, data sources)
- [ ] 9.1.10 Maintain changelog for all production releases

### 9.2 User Documentation

- [ ] 9.2.1 Create user guide for interpreting AUCS scores
- [ ] 9.2.2 Document subscores and their meanings (EA, LCA, MUHAA, etc.)
- [ ] 9.2.3 Create example use cases (urban planning, real estate, equity analysis)
- [ ] 9.2.4 Document data sources and their update cadence
- [ ] 9.2.5 Create visualization examples (maps, charts, dashboards)
- [ ] 9.2.6 Document limitations and caveats (what AUCS doesn't measure)
- [ ] 9.2.7 Create tutorial notebooks (Jupyter) for data analysis
- [ ] 9.2.8 Document export formats and schemas (Parquet, GeoJSON)
- [ ] 9.2.9 Create API reference (if exposing scores via API)
- [ ] 9.2.10 Publish documentation website (MkDocs Material or similar)

### 9.3 Team Training

- [ ] 9.3.1 Conduct training session on AUCS model and methodology
- [ ] 9.3.2 Train team on parameter configuration and tuning
- [ ] 9.3.3 Train team on pipeline operations (run, monitor, troubleshoot)
- [ ] 9.3.4 Train team on data quality checks and validation
- [ ] 9.3.5 Conduct table-top exercises (simulate failures, practice response)
- [ ] 9.3.6 Create video walkthroughs for common tasks
- [ ] 9.3.7 Document on-call procedures and escalation paths
- [ ] 9.3.8 Create knowledge base for tribal knowledge
- [ ] 9.3.9 Conduct quarterly refresher training
- [ ] 9.3.10 Maintain training materials and update as system evolves

## 10. Calibration and Validation (MEDIUM PRIORITY)

### 10.1 Ground Truth Validation

- [ ] 10.1.1 Identify ground truth datasets (existing walkability scores, transit access)
- [ ] 10.1.2 Compare AUCS with Walk Score at sample locations (correlation analysis)
- [ ] 10.1.3 Compare AUCS with AllTransit at sample locations
- [ ] 10.1.4 Validate essentials access with USDA Food Access Research Atlas
- [ ] 10.1.5 Validate transit access with agency GTFS-based metrics
- [ ] 10.1.6 Survey sample locations (field visits or Street View validation)
- [ ] 10.1.7 Document validation methodology and results
- [ ] 10.1.8 Identify systematic biases (urban vs rural, mountain vs plains)
- [ ] 10.1.9 Adjust parameters based on validation findings
- [ ] 10.1.10 Re-run validation after parameter adjustments

### 10.2 Parameter Calibration

- [ ] 10.2.1 Conduct sensitivity analysis (vary parameters, measure output changes)
- [ ] 10.2.2 Calibrate decay parameters (alpha) to match observed travel behavior
- [ ] 10.2.3 Calibrate satiation curves (kappa) to match diminishing returns
- [ ] 10.2.4 Calibrate subscore weights based on stakeholder input
- [ ] 10.2.5 Validate CES elasticity (rho) matches substitution patterns
- [ ] 10.2.6 Calibrate VOT (value of time) to regional studies
- [ ] 10.2.7 Calibrate mode constants (beta0) to mode share data
- [ ] 10.2.8 Document calibration process and rationale for parameter values
- [ ] 10.2.9 Create parameter uncertainty ranges (confidence intervals)
- [ ] 10.2.10 Freeze parameters for production release (version 1.0)

### 10.3 Quality Assurance

- [ ] 10.3.1 Define QA metrics (score distributions, coverage, completeness)
- [ ] 10.3.2 Create automated QA report (run after each pipeline execution)
- [ ] 10.3.3 Check for anomalies (outliers, sudden changes from previous run)
- [ ] 10.3.4 Validate spatial patterns (urban cores should score high)
- [ ] 10.3.5 Validate metro-level comparisons (known differences between cities)
- [ ] 10.3.6 Check for data gaps (missing hexes, zero scores where unexpected)
- [ ] 10.3.7 Validate mathematical properties (monotonicity, scale invariance)
- [ ] 10.3.8 Create QA dashboard with summary statistics and visuals
- [ ] 10.3.9 Document QA thresholds (when to investigate vs accept)
- [ ] 10.3.10 Implement automated QA gates (fail pipeline if QA thresholds not met)

---

## 11. Interactive UI Deployment (25 tasks)

### 11.1 UI Server Deployment

- [ ] 11.1.1 Deploy Dash application with Gunicorn (4 workers for 16-core machine)
- [ ] 11.1.2 Configure worker timeout (300s for long callbacks)
- [ ] 11.1.3 Set up Nginx reverse proxy for UI
- [ ] 11.1.4 Configure SSL/TLS with Let's Encrypt (automatic renewal)
- [ ] 11.1.5 Set up HTTPS redirect (force SSL)
- [ ] 11.1.6 Configure gzip compression for API responses
- [ ] 11.1.7 Set up static asset caching (CSS, JS, images)
- [ ] 11.1.8 Configure CORS if API on different domain
- [ ] 11.1.9 Test UI deployment in staging environment
- [ ] 11.1.10 Document UI deployment procedures

### 11.2 Cache Layer Deployment

- [ ] 11.2.1 Deploy DiskCache backend (50GB limit) or Redis if multi-server
- [ ] 11.2.2 Configure cache TTLs per data source (24h-90d)
- [ ] 11.2.3 Implement cache warming on startup (common queries)
- [ ] 11.2.4 Test cache hit rates (target >80%)
- [ ] 11.2.5 Monitor cache size and eviction rate
- [ ] 11.2.6 Test cache refresh functionality in UI
- [ ] 11.2.7 Validate cache invalidation on graph rebuild
- [ ] 11.2.8 Document cache management procedures

### 11.3 UI Testing

- [ ] 11.3.1 Test UI on desktop (Chrome, Firefox, Safari, Edge)
- [ ] 11.3.2 Test UI on tablet (iPad, Android tablets)
- [ ] 11.3.3 Test UI on mobile (iOS, Android phones)
- [ ] 11.3.4 Test touch interactions (pinch-zoom, tap, swipe)
- [ ] 11.3.5 Load test with 10 concurrent users (measure response times)
- [ ] 11.3.6 Test WebGL rendering with 100K+ hexes
- [ ] 11.3.7 Test shareable URLs (encode filters in URL)
- [ ] 11.3.8 Test export functions (PNG, PDF, GeoJSON, CSV)
- [ ] 11.3.9 Test UI with slow network (3G throttling)

### 11.4 UI Security and Documentation

- [ ] 11.4.1 Test input sanitization (prevent XSS attacks)
- [ ] 11.4.2 Validate CSRF protection on forms
- [ ] 11.4.3 Test rate limiting (100 req/min per user)
- [ ] 11.4.4 Test authentication system if enabled
- [ ] 11.4.5 Record video tutorial (5-minute walkthrough)
- [ ] 11.4.6 Create user guide for UI (navigation, filtering, export)
- [ ] 11.4.7 Test accessibility (WCAG AA compliance, screen readers)
- [ ] 11.4.8 Validate all tooltips and help text

---

## 12. Mathematical Validation & Calibration (25 tasks)

### 12.1 CES and Satiation Testing

- [ ] 12.1.1 Unit test CES aggregation with known inputs
- [ ] 12.1.2 Property test: CES monotonicity (more amenities → higher V_c)
- [ ] 12.1.3 Test CES numerical stability (no overflow with large inputs)
- [ ] 12.1.4 Test CES limits (ρ→0 Cobb-Douglas, ρ→1 linear)
- [ ] 12.1.5 Unit test satiation curves with anchor points
- [ ] 12.1.6 Property test: satiation asymptotes to 100
- [ ] 12.1.7 Test satiation with extreme cases (V_c=0, V_c→∞)
- [ ] 12.1.8 Validate κ_c computation from anchors (κ_c > 0)

### 12.2 Quality Scoring and Diversity

- [ ] 12.2.1 Unit test Q_a components (size, popularity, brand, heritage)
- [ ] 12.2.2 Test Q_a ranges (all scores in [0, 100])
- [ ] 12.2.3 Test brand deduplication (verify weight reduction)
- [ ] 12.2.4 Test opening hours bonus logic
- [ ] 12.2.5 Unit test Shannon diversity index
- [ ] 12.2.6 Test diversity with monoculture vs mixed categories
- [ ] 12.2.7 Validate diversity bonus multiplier (1.0-1.2×)

### 12.3 Subscore Validation

- [ ] 12.3.1 Validate all 7 subscores in [0, 100] range (EA, LCA, MUHAA, JEA, MORR, CTE, SOU)
- [ ] 12.3.2 Validate subscore weights sum to 100
- [ ] 12.3.3 Test each subscore with synthetic data (known outcomes)
- [ ] 12.3.4 Property test: monotonicity (more access → higher scores)
- [ ] 12.3.5 Test edge cases (zero amenities, unreachable locations)
- [ ] 12.3.6 Validate no NaN or Inf values in any subscore
- [ ] 12.3.7 Compare subscores across metros (sanity checks)

### 12.4 Parameter Calibration

- [ ] 12.4.1 Calibrate ρ_c (CES elasticity) per category from expert judgment
- [ ] 12.4.2 Calibrate κ_c (satiation) from anchor points (e.g., 5 groceries → 80%)
- [ ] 12.4.3 Calibrate MORR component weights (C₁-C₅, default equal)
- [ ] 12.4.4 Calibrate MUHAA hub mass weights (population, GDP, POI, culture)
- [ ] 12.4.5 Conduct sensitivity analysis (vary parameters ±20%, measure output changes)
- [ ] 12.4.6 Validate calibrated parameters with pilot test (Boulder County)
- [ ] 12.4.7 Document calibration methodology and rationale
- [ ] 12.4.8 Freeze parameters for v1.0 release
- [ ] 12.4.9 Create parameter uncertainty documentation

---

## 13. Full Model Performance Testing (25 tasks)

### 13.1 Pipeline Benchmarking

- [ ] 13.1.1 Benchmark full pipeline with all 7 subscores on pilot region (Boulder County)
- [ ] 13.1.2 Measure time per subscore (EA, LCA, MUHAA, JEA, MORR, CTE, SOU)
- [ ] 13.1.3 Identify bottleneck subscores (likely MUHAA, CTE with routing)
- [ ] 13.1.4 Profile each subscore with cProfile or py-spy
- [ ] 13.1.5 Measure peak memory usage per subscore
- [ ] 13.1.6 Document resource requirements (CPU, RAM, disk I/O)

### 13.2 Full-Scale Testing

- [ ] 13.2.1 Run full pipeline on all 3 states (CO/UT/ID, ~1M hexes)
- [ ] 13.2.2 Monitor execution: logs, metrics, alerts
- [ ] 13.2.3 Validate total run time <8 hours (target)
- [ ] 13.2.4 Validate memory usage <16GB (target)
- [ ] 13.2.5 Check temp disk usage (ensure <100GB)
- [ ] 13.2.6 Validate all subscores computed for all hexes
- [ ] 13.2.7 Run QA report on full outputs
- [ ] 13.2.8 Generate summary statistics per metro

### 13.3 Performance Optimization

- [ ] 13.3.1 Optimize MUHAA routing queries (cache common hub OD pairs)
- [ ] 13.3.2 Optimize CTE path analysis (limit paths per hex)
- [ ] 13.3.3 Parallelize subscore computation where possible (independent subscores)
- [ ] 13.3.4 Use Polars or DuckDB for heavy aggregations
- [ ] 13.3.5 Optimize Parquet I/O (compression, partitioning)
- [ ] 13.3.6 Profile and optimize hot loops with Numba JIT
- [ ] 13.3.7 Test optimizations (verify correctness, measure speedup)
- [ ] 13.3.8 Document performance improvements achieved

### 13.4 UI Performance with Full Dataset

- [ ] 13.4.1 Load full 1M hex dataset into UI
- [ ] 13.4.2 Test viewport queries with 100K+ hexes visible
- [ ] 13.4.3 Test zoom/pan performance (target <500ms)
- [ ] 13.4.4 Test filter performance with full dataset
- [ ] 13.4.5 Test choropleth rendering at all zoom levels
- [ ] 13.4.6 Validate WebGL rendering with 1M hexes (via aggregation)
- [ ] 13.4.7 Test UI memory usage in browser (<2GB)
- [ ] 13.4.8 Optimize UI if needed (more aggressive aggregation)
- [ ] 13.4.9 Load test UI with 10 concurrent users + full dataset

---

**Total Tasks:** 385 across 13 major workstreams (75 tasks added)
**Critical Path:** External Services (1.1-1.3) → Data Pipeline (2.1-2.3) → Integration Testing (3.1-3.3) → UI Deployment (11) → Full Model Testing (13)
**Estimated Timeline:** 8-10 weeks with dedicated team (expanded scope)
