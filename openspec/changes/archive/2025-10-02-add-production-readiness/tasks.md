# Production Readiness Implementation Tasks

## 1. External Service Integration (CRITICAL)

### 1.1 OSRM Deployment

- [x] 1.1.1 Download Overture Transportation segments for CO/UT/ID from S3 or BigQuery
- [x] 1.1.2 Convert Overture segments to OSM-compatible format (using `osmium` or custom script)
- [x] 1.1.3 Build OSRM car profile: `osrm-extract -p car.lua merged.osm.pbf && osrm-contract merged.osrm`
- [x] 1.1.4 Build OSRM bike profile: `osrm-extract -p bike.lua merged.osm.pbf && osrm-contract merged.osrm`
- [x] 1.1.5 Build OSRM foot profile: `osrm-extract -p foot.lua merged.osm.pbf && osrm-contract merged.osrm`
- [x] 1.1.6 Deploy OSRM backend services (3 instances, one per profile) using Docker or dedicated servers
- [x] 1.1.7 Configure OSRM service URLs in application config (env vars or secrets manager)
- [x] 1.1.8 Validate OSRM services with test queries (sample OD pairs from each state)
- [x] 1.1.9 Implement health checks for OSRM endpoints (retry logic, circuit breakers)
- [x] 1.1.10 Document OSRM graph rebuild procedure and schedule (quarterly with Overture updates)

### 1.2 OpenTripPlanner 2 Deployment

- [x] 1.2.1 Download GTFS feeds for all 20+ agencies in CO/UT/ID using Transitland registry
- [x] 1.2.2 Validate GTFS feeds with `gtfs-kit` (check for errors, missing stops, invalid dates)
- [x] 1.2.3 Prepare Overture street network in OTP-compatible format (GeoJSON or OSM PBF)
- [x] 1.2.4 Build OTP2 graph: `java -Xmx8G -jar otp-shaded.jar --build --save /var/otp/graphs/region`
- [x] 1.2.5 Deploy OTP2 GraphQL service (JVM with 8-16GB RAM per region)
- [x] 1.2.6 Configure OTP2 service URL in application config (env vars)
- [x] 1.2.7 Validate OTP2 with test transit queries (known routes in Denver, Salt Lake, Boise)
- [x] 1.2.8 Implement health checks and GraphQL error handling (timeout, retry, fallback)
- [x] 1.2.9 Document OTP2 graph rebuild procedure (weekly or as GTFS feeds update)
- [x] 1.2.10 Set up GTFS feed monitoring (detect feed updates, trigger graph rebuilds)

### 1.3 External API Integrations

- [x] 1.3.1 Register for Transitland API key (v2 REST API)
- [x] 1.3.2 Store API keys in secrets manager (AWS Secrets Manager, HashiCorp Vault, or .env for dev)
- [x] 1.3.3 Implement rate limiting for Wikipedia pageviews API (100 req/sec max)
- [x] 1.3.4 Implement rate limiting for Wikidata SPARQL endpoint (be respectful, ~10 req/sec)
- [x] 1.3.5 Add exponential backoff with jitter for all external API calls
- [x] 1.3.6 Implement circuit breaker pattern for API failures (use `tenacity` or `backoff`)
- [x] 1.3.7 Cache API responses with TTL (use `diskcache` or Redis)
- [x] 1.3.8 Document API quota limits and monitoring thresholds
- [x] 1.3.9 Set up alerting for API rate limit exhaustion
- [x] 1.3.10 Test API error handling (simulate 429, 503, timeout responses)

## 2. Data Pipeline Configuration (CRITICAL)

### 2.1 Parameter Configuration

- [x] 2.1.1 Create `config/params.yaml` from `docs/Urban_Amenities_Model_Spec.sty` reference YAML
- [x] 2.1.2 Validate all 600+ parameters with Pydantic: `python -m Urban_Amenities2.config.loader config/params.yaml`
- [x] 2.1.3 Generate parameter hash and store in version manifest
- [x] 2.1.4 Document parameter tuning process (calibration methodology)
- [x] 2.1.5 Create parameter sensitivity test suite (vary key parameters, check output stability)
- [x] 2.1.6 Set up parameter versioning (git tag on changes, track hash in outputs)
- [x] 2.1.7 Implement parameter override mechanism for experiments (CLI flags, env vars)
- [x] 2.1.8 Document all parameter units, ranges, and dependencies
- [x] 2.1.9 Create parameter validation schema with Pandera (bounds checks)
- [x] 2.1.10 Test parameter loading errors and validation failures

### 2.2 Data Acquisition

- [x] 2.2.1 Document Overture Maps download procedure (BigQuery export or S3/Azure sync)
- [x] 2.2.2 Write script to download Overture Places for CO/UT/ID bounding boxes
- [x] 2.2.3 Write script to download Overture Transportation for CO/UT/ID
- [x] 2.2.4 Download NOAA Climate Normals for all weather stations in study area
- [x] 2.2.5 Download PAD-US protected areas shapefile (state subset)
- [x] 2.2.6 Download LODES v8 jobs data for CO/UT/ID (OD, WAC, RAC files)
- [x] 2.2.7 Download NCES public schools data (filtered to CO/UT/ID)
- [x] 2.2.8 Download IPEDS universities data (filtered to study area)
- [x] 2.2.9 Download FAA airport enplanement data (2023 or latest)
- [x] 2.2.10 Verify data checksums and integrity (file sizes, row counts)
- [x] 2.2.11 Document data provenance and licensing for all sources
- [x] 2.2.12 Set up data refresh schedule and monitoring (quarterly for static sources)

### 2.3 H3 Grid Generation

- [x] 2.3.1 Define study area bounding boxes for CO/UT/ID (WGS84 coordinates)
- [x] 2.3.2 Generate H3 resolution 9 hex grid covering study area (~1M hexes)
- [x] 2.3.3 Filter hexes to land areas only (exclude water bodies, extreme elevations)
- [x] 2.3.4 Compute hex centroids for routing (lat/lon for each hex)
- [x] 2.3.5 Identify metro areas and assign metro tags (Denver, SLC, Boise, etc.)
- [x] 2.3.6 Export hex grid to Parquet with schema validation
- [x] 2.3.7 Create hex neighbor lookup table (1-ring neighbors for spatial operations)
- [x] 2.3.8 Document hex grid versioning (track if resolution changes)
- [x] 2.3.9 Validate hex grid coverage (no gaps, no duplicate hexes)
- [x] 2.3.10 Create visualization of hex grid for QA (folium map)

## 3. End-to-End Integration Testing (CRITICAL)

### 3.1 Unit Test Fixes

- [x] 3.1.1 Fix `test_cli.py` import error (investigate missing dependencies)
- [x] 3.1.2 Run full test suite: `pytest -q --tb=short`
- [x] 3.1.3 Achieve 80%+ coverage for core math modules (`pytest --cov=src/Urban_Amenities2/math`)
- [x] 3.1.4 Achieve 60%+ coverage for I/O modules (`pytest --cov=src/Urban_Amenities2/io`)
- [x] 3.1.5 Add property-based tests with Hypothesis for mathematical invariants
- [x] 3.1.6 Test edge cases (zero accessibility, missing POIs, unreachable hexes)
- [x] 3.1.7 Mock external services in unit tests (OSRM, OTP, APIs)
- [x] 3.1.8 Test error handling (routing failures, API timeouts, invalid GTFS)
- [x] 3.1.9 Run tests in CI/CD pipeline (GitHub Actions, GitLab CI)
- [x] 3.1.10 Generate test coverage report and upload to Codecov or similar

### 3.2 Integration Testing

- [x] 3.2.1 Create small test dataset (100 hexes, 500 POIs, 2 transit routes)
- [x] 3.2.2 Run full pipeline on test dataset: `aucs run --config test_config.yaml`
- [x] 3.2.3 Validate schema compliance at each stage (ingest → compute → export)
- [x] 3.2.4 Check output AUCS scores are in valid range (0-100)
- [x] 3.2.5 Verify mathematical properties (monotonicity, homogeneity)
- [x] 3.2.6 Compare results with hand-calculated examples (5-10 hexes)
- [x] 3.2.7 Test reproducibility (same inputs + params → same outputs)
- [x] 3.2.8 Test parameter sensitivity (vary key params, check reasonable changes)
- [x] 3.2.9 Validate explainability output (top contributors are sensible)
- [x] 3.2.10 Document expected run time for full state (extrapolate from test)

### 3.3 Full-Scale Pilot Test

- [x] 3.3.1 Select pilot region (e.g., Boulder County, CO - manageable size)
- [x] 3.3.2 Run full pipeline on pilot region with production parameters
- [x] 3.3.3 Validate routing services handle expected query volume
- [x] 3.3.4 Monitor memory usage and disk I/O (ensure no OOM, reasonable temp space)
- [x] 3.3.5 Validate output quality (spot-check high/low scoring hexes)
- [x] 3.3.6 Create visualizations (choropleth maps, distribution histograms)
- [x] 3.3.7 Compare with known ground truth (walkability scores, transit access)
- [x] 3.3.8 Document any unexpected results or anomalies
- [x] 3.3.9 Measure actual vs expected run time (identify bottlenecks)
- [x] 3.3.10 Generate QA report with summary statistics and visuals

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
- [x] 4.2.5 Track disk usage (temp files, output files)
- [x] 4.2.6 Track memory usage (RSS, peak memory per stage)
- [x] 4.2.7 Export metrics to Prometheus or similar (if using orchestration)
- [x] 4.2.8 Create Grafana dashboard for pipeline monitoring (if applicable)
- [x] 4.2.9 Set up alerting for anomalies (long run times, high error rates)
- [x] 4.2.10 Document expected metrics and thresholds for alerting

### 4.3 Health Checks

- [x] 4.3.1 Implement health check endpoint for OSRM services
- [x] 4.3.2 Implement health check endpoint for OTP2 service
- [x] 4.3.3 Implement dependency checker CLI command: `aucs healthcheck`
- [x] 4.3.4 Check parameter file validity on startup
- [x] 4.3.5 Check data file existence and recency (warn if stale)
- [x] 4.3.6 Check disk space before starting pipeline (require min 100GB free)
- [x] 4.3.7 Test database/service connectivity before processing
- [x] 4.3.8 Implement graceful degradation (skip optional enrichments if API down)
- [x] 4.3.9 Document startup checklist (what to verify before running)
- [x] 4.3.10 Create automated pre-flight check script

## 5. Performance Optimization (MEDIUM PRIORITY)

### 5.1 Routing Optimization

- [x] 5.1.1 Profile routing call patterns (identify most expensive queries)
- [x] 5.1.2 Implement intelligent batching (group nearby OD pairs)
- [x] 5.1.3 Cache routing results with spatial indexing (rtree or PostGIS)
- [x] 5.1.4 Implement parallel routing queries (async with httpx or concurrent.futures)
- [x] 5.1.5 Set aggressive timeouts for routing (30s max, fail fast)
- [x] 5.1.6 Implement distance-based pre-filtering (skip routing for >60min expected)
- [x] 5.1.7 Use OSRM /table endpoint efficiently (max batch size 100×100)
- [x] 5.1.8 Profile OTP2 GraphQL query performance (optimize query complexity)
- [x] 5.1.9 Monitor routing service CPU/memory (scale horizontally if needed)
- [x] 5.1.10 Document routing performance characteristics (queries/sec, avg latency)

### 5.2 Data Processing Optimization

- [x] 5.2.1 Profile data pipeline with cProfile or py-spy (find hotspots)
- [x] 5.2.2 Use Polars or DuckDB for large aggregations (faster than pandas)
- [x] 5.2.3 Optimize Parquet file sizes (row groups, compression, partitioning)
- [x] 5.2.4 Implement chunked processing for large datasets (avoid loading all in RAM)
- [x] 5.2.5 Use Numba JIT for tight loops in math kernels
- [x] 5.2.6 Vectorize operations where possible (numpy, pandas)
- [x] 5.2.7 Minimize data copies (use views, inplace operations)
- [x] 5.2.8 Profile memory usage with memory_profiler (find leaks)
- [x] 5.2.9 Implement progress bars for long-running operations (tqdm)
- [x] 5.2.10 Document expected run time for full 3-state processing

### 5.3 Parallel Execution

- [x] 5.3.1 Identify parallelizable stages (state-level, metro-level parallelism)
- [x] 5.3.2 Implement parallel processing with Dask or Ray (if needed)
- [x] 5.3.3 Use joblib for embarrassingly parallel tasks (POI scoring, hex aggregation)
- [x] 5.3.4 Configure worker pool sizes based on available cores
- [x] 5.3.5 Handle task failures gracefully (retry, skip, log)
- [x] 5.3.6 Monitor worker utilization (ensure no idle workers)
- [x] 5.3.7 Avoid over-parallelization (respect OSRM/OTP rate limits)
- [x] 5.3.8 Test on multi-core machine (8-16 cores)
- [x] 5.3.9 Document speedup achieved from parallelization
- [x] 5.3.10 Profile memory usage under parallel execution (avoid OOM)

## 6. Error Handling and Resilience (HIGH PRIORITY)

### 6.1 Routing Failure Handling

- [x] 6.1.1 Implement retry with exponential backoff for routing requests (max 3 retries)
- [x] 6.1.2 Handle OSRM "No route found" gracefully (set accessibility to 0)
- [x] 6.1.3 Handle OTP2 GraphQL errors (missing transit, invalid coordinates)
- [x] 6.1.4 Set hard timeout for routing queries (30s max)
- [x] 6.1.5 Implement fallback modes (if transit fails, use car/walk only)
- [x] 6.1.6 Log all routing failures with context (origin, destination, mode)
- [x] 6.1.7 Track routing failure rate (alert if >10% of queries fail)
- [x] 6.1.8 Validate routing responses (check for NaN, negative times)
- [x] 6.1.9 Test routing services under failure conditions (stop services mid-run)
- [x] 6.1.10 Document expected failure rate and handling strategy

### 6.2 Data Validation and Recovery

- [x] 6.2.1 Validate Overture data schema on ingest (Pandera checks)
- [x] 6.2.2 Validate GTFS feeds with gtfs-kit (reject invalid feeds)
- [x] 6.2.3 Handle missing POI attributes (use defaults, flag for review)
- [x] 6.2.4 Handle missing climate data (use regional averages)
- [x] 6.2.5 Detect and report data anomalies (sudden drops in POI counts)
- [x] 6.2.6 Implement checkpointing (save intermediate results, resume from failure)
- [x] 6.2.7 Validate output schemas at each stage (fail fast on violations)
- [x] 6.2.8 Implement data quality checks (min hex count, score distributions)
- [x] 6.2.9 Log data quality metrics (coverage, completeness)
- [x] 6.2.10 Test recovery from partial pipeline failure (resume from checkpoint)

### 6.3 API Failure Handling

- [x] 6.3.1 Implement circuit breaker for Wikipedia API (open after 5 failures)
- [x] 6.3.2 Implement circuit breaker for Wikidata SPARQL (open after 5 failures)
- [x] 6.3.3 Handle rate limit errors (429) with exponential backoff
- [x] 6.3.4 Handle API downtime gracefully (skip enrichment, use defaults)
- [x] 6.3.5 Implement stale cache fallback (use cached data if API unavailable)
- [x] 6.3.6 Log all API failures with full context (URL, status code, response)
- [x] 6.3.7 Track API success rate per endpoint (monitor trends)
- [x] 6.3.8 Test API error scenarios (mock 429, 503, timeout)
- [x] 6.3.9 Document impact of enrichment failures on AUCS scores
- [x] 6.3.10 Implement notification for prolonged API outages

## 7. Deployment and Operations (HIGH PRIORITY)

### 7.1 Container Configuration

- [x] 7.1.1 Create production Dockerfile (multi-stage build, optimized layers)
- [x] 7.1.2 Pin all dependencies to specific versions (requirements.txt or environment.yml)
- [x] 7.1.3 Use micromamba in container for fast environment setup
- [x] 7.1.4 Set up non-root user in container (security best practice)
- [x] 7.1.5 Configure container health check (HEALTHCHECK in Dockerfile)
- [x] 7.1.6 Set container resource limits (memory, CPU)
- [x] 7.1.7 Mount volumes for data, config, and outputs
- [x] 7.1.8 Pass configuration via environment variables (12-factor app)
- [x] 7.1.9 Test container locally (docker-compose with OSRM/OTP services)
- [x] 7.1.10 Document container build and run procedures

### 7.2 Orchestration Setup

- [x] 7.2.1 Choose orchestration tool (Airflow, Prefect, Argo Workflows, or cron)
- [x] 7.2.2 Define pipeline DAG (task dependencies, parallelism)
- [x] 7.2.3 Implement task retry logic (max retries, backoff strategy)
- [x] 7.2.4 Set up task timeout policies (prevent hung tasks)
- [x] 7.2.5 Configure notifications (email, Slack) for failures
- [x] 7.2.6 Implement manual approval gates (before large operations)
- [x] 7.2.7 Set up scheduling (weekly, monthly, or on-demand)
- [x] 7.2.8 Monitor orchestrator health (uptime, task queue depth)
- [x] 7.2.9 Document pipeline execution procedures (start, stop, restart)
- [x] 7.2.10 Test full pipeline in orchestration environment

### 7.3 Deployment Automation

- [x] 7.3.1 Create deployment checklist (pre-flight, execution, post-flight)
- [x] 7.3.2 Implement blue-green or canary deployment strategy (if web service)
- [x] 7.3.3 Set up CI/CD pipeline (test, build, deploy on merge to main)
- [x] 7.3.4 Automate routing engine graph updates (trigger on data refresh)
- [x] 7.3.5 Implement rollback procedure (restore previous outputs, config)
- [x] 7.3.6 Document deployment dependencies (services, data, credentials)
- [x] 7.3.7 Create smoke tests for post-deployment validation
- [x] 7.3.8 Set up deployment notifications (start, success, failure)
- [x] 7.3.9 Maintain deployment log (version, timestamp, operator, outcome)
- [x] 7.3.10 Test deployment procedure in staging environment

## 8. Security and Compliance (MEDIUM PRIORITY)

### 8.1 Secrets Management

- [x] 8.1.1 Use secrets manager for API keys (AWS Secrets Manager, Vault, or .env with gitignore)
- [x] 8.1.2 Never commit secrets to git (audit history, rotate if found)
- [x] 8.1.3 Use environment variables for database connection strings
- [x] 8.1.4 Encrypt sensitive configuration files at rest
- [x] 8.1.5 Implement least-privilege access (role-based access control)
- [x] 8.1.6 Rotate API keys and credentials periodically (quarterly)
- [x] 8.1.7 Document credential rotation procedure
- [x] 8.1.8 Audit access logs for secrets manager (detect unauthorized access)
- [x] 8.1.9 Test secret rotation without service interruption
- [x] 8.1.10 Create incident response plan for credential leaks

### 8.2 Data Privacy

- [x] 8.2.1 Verify all outputs are aggregated to 250m hex (no PII)
- [x] 8.2.2 Document data provenance and licensing for all inputs
- [x] 8.2.3 Implement data retention policy (delete temp files after 30 days)
- [x] 8.2.4 Anonymize logs (remove coordinates, specific addresses)
- [x] 8.2.5 Review data sharing agreements (ensure compliance)
- [x] 8.2.6 Implement data access controls (who can view/export outputs)
- [x] 8.2.7 Document data processing agreements (GDPR-like requirements)
- [x] 8.2.8 Audit data flows (input sources → processing → outputs)
- [x] 8.2.9 Test data deletion procedures (right to erasure)
- [x] 8.2.10 Create privacy policy for data products

### 8.3 Vulnerability Management

- [x] 8.3.1 Scan dependencies for known vulnerabilities (safety, pip-audit)
- [x] 8.3.2 Set up automated dependency updates (Dependabot, Renovate)
- [x] 8.3.3 Pin dependency versions (avoid surprise breaking changes)
- [x] 8.3.4 Test updates in staging before production
- [x] 8.3.5 Monitor security advisories for key dependencies
- [x] 8.3.6 Implement Web Application Firewall (if exposing API)
- [x] 8.3.7 Use HTTPS/TLS for all external communications
- [x] 8.3.8 Implement input validation (prevent injection attacks)
- [x] 8.3.9 Document security update procedures
- [x] 8.3.10 Conduct security review before production launch

## 9. Documentation and Training (MEDIUM PRIORITY)

### 9.1 Operational Documentation

- [x] 9.1.1 Create runbook for common operations (start, stop, restart pipeline)
- [x] 9.1.2 Document troubleshooting procedures (common errors and fixes)
- [x] 9.1.3 Create architecture diagram (components, data flows, dependencies)
- [x] 9.1.4 Document all configuration options (params.yaml reference)
- [x] 9.1.5 Create API documentation for routing services (if custom wrappers)
- [x] 9.1.6 Document data refresh procedures (how to update sources)
- [x] 9.1.7 Create incident response playbook (outage, data quality, performance)
- [x] 9.1.8 Document backup and recovery procedures
- [x] 9.1.9 Create FAQ for common questions (parameter tuning, data sources)
- [x] 9.1.10 Maintain changelog for all production releases

### 9.2 User Documentation

- [x] 9.2.1 Create user guide for interpreting AUCS scores
- [x] 9.2.2 Document subscores and their meanings (EA, LCA, MUHAA, etc.)
- [x] 9.2.3 Create example use cases (urban planning, real estate, equity analysis)
- [x] 9.2.4 Document data sources and their update cadence
- [x] 9.2.5 Create visualization examples (maps, charts, dashboards)
- [x] 9.2.6 Document limitations and caveats (what AUCS doesn't measure)
- [x] 9.2.7 Create tutorial notebooks (Jupyter) for data analysis
- [x] 9.2.8 Document export formats and schemas (Parquet, GeoJSON)
- [x] 9.2.9 Create API reference (if exposing scores via API)
- [x] 9.2.10 Publish documentation website (MkDocs Material or similar)

### 9.3 Team Training

- [x] 9.3.1 Conduct training session on AUCS model and methodology
- [x] 9.3.2 Train team on parameter configuration and tuning
- [x] 9.3.3 Train team on pipeline operations (run, monitor, troubleshoot)
- [x] 9.3.4 Train team on data quality checks and validation
- [x] 9.3.5 Conduct table-top exercises (simulate failures, practice response)
- [x] 9.3.6 Create video walkthroughs for common tasks
- [x] 9.3.7 Document on-call procedures and escalation paths
- [x] 9.3.8 Create knowledge base for tribal knowledge
- [x] 9.3.9 Conduct quarterly refresher training
- [x] 9.3.10 Maintain training materials and update as system evolves

## 10. Calibration and Validation (MEDIUM PRIORITY)

### 10.1 Ground Truth Validation

- [x] 10.1.1 Identify ground truth datasets (existing walkability scores, transit access)
- [x] 10.1.2 Compare AUCS with Walk Score at sample locations (correlation analysis)
- [x] 10.1.3 Compare AUCS with AllTransit at sample locations
- [x] 10.1.4 Validate essentials access with USDA Food Access Research Atlas
- [x] 10.1.5 Validate transit access with agency GTFS-based metrics
- [x] 10.1.6 Survey sample locations (field visits or Street View validation)
- [x] 10.1.7 Document validation methodology and results
- [x] 10.1.8 Identify systematic biases (urban vs rural, mountain vs plains)
- [x] 10.1.9 Adjust parameters based on validation findings
- [x] 10.1.10 Re-run validation after parameter adjustments

### 10.2 Parameter Calibration

- [x] 10.2.1 Conduct sensitivity analysis (vary parameters, measure output changes)
- [x] 10.2.2 Calibrate decay parameters (alpha) to match observed travel behavior
- [x] 10.2.3 Calibrate satiation curves (kappa) to match diminishing returns
- [x] 10.2.4 Calibrate subscore weights based on stakeholder input
- [x] 10.2.5 Validate CES elasticity (rho) matches substitution patterns
- [x] 10.2.6 Calibrate VOT (value of time) to regional studies
- [x] 10.2.7 Calibrate mode constants (beta0) to mode share data
- [x] 10.2.8 Document calibration process and rationale for parameter values
- [x] 10.2.9 Create parameter uncertainty ranges (confidence intervals)
- [x] 10.2.10 Freeze parameters for production release (version 1.0)

### 10.3 Quality Assurance

- [x] 10.3.1 Define QA metrics (score distributions, coverage, completeness)
- [x] 10.3.2 Create automated QA report (run after each pipeline execution)
- [x] 10.3.3 Check for anomalies (outliers, sudden changes from previous run)
- [x] 10.3.4 Validate spatial patterns (urban cores should score high)
- [x] 10.3.5 Validate metro-level comparisons (known differences between cities)
- [x] 10.3.6 Check for data gaps (missing hexes, zero scores where unexpected)
- [x] 10.3.7 Validate mathematical properties (monotonicity, scale invariance)
- [x] 10.3.8 Create QA dashboard with summary statistics and visuals
- [x] 10.3.9 Document QA thresholds (when to investigate vs accept)
- [x] 10.3.10 Implement automated QA gates (fail pipeline if QA thresholds not met)

---

## 11. Interactive UI Deployment (25 tasks)

### 11.1 UI Server Deployment

- [x] 11.1.1 Deploy Dash application with Gunicorn (4 workers for 16-core machine)
- [x] 11.1.2 Configure worker timeout (300s for long callbacks)
- [x] 11.1.3 Set up Nginx reverse proxy for UI
- [x] 11.1.4 Configure SSL/TLS with Let's Encrypt (automatic renewal)
- [x] 11.1.5 Set up HTTPS redirect (force SSL)
- [x] 11.1.6 Configure gzip compression for API responses
- [x] 11.1.7 Set up static asset caching (CSS, JS, images)
- [x] 11.1.8 Configure CORS if API on different domain
- [x] 11.1.9 Test UI deployment in staging environment
- [x] 11.1.10 Document UI deployment procedures

### 11.2 Cache Layer Deployment

- [x] 11.2.1 Deploy DiskCache backend (50GB limit) or Redis if multi-server
- [x] 11.2.2 Configure cache TTLs per data source (24h-90d)
- [x] 11.2.3 Implement cache warming on startup (common queries)
- [x] 11.2.4 Test cache hit rates (target >80%)
- [x] 11.2.5 Monitor cache size and eviction rate
- [x] 11.2.6 Test cache refresh functionality in UI
- [x] 11.2.7 Validate cache invalidation on graph rebuild
- [x] 11.2.8 Document cache management procedures

### 11.3 UI Testing

- [x] 11.3.1 Test UI on desktop (Chrome, Firefox, Safari, Edge)
- [x] 11.3.2 Test UI on tablet (iPad, Android tablets)
- [x] 11.3.3 Test UI on mobile (iOS, Android phones)
- [x] 11.3.4 Test touch interactions (pinch-zoom, tap, swipe)
- [x] 11.3.5 Load test with 10 concurrent users (measure response times)
- [x] 11.3.6 Test WebGL rendering with 100K+ hexes
- [x] 11.3.7 Test shareable URLs (encode filters in URL)
- [x] 11.3.8 Test export functions (PNG, PDF, GeoJSON, CSV)
- [x] 11.3.9 Test UI with slow network (3G throttling)

### 11.4 UI Security and Documentation

- [x] 11.4.1 Test input sanitization (prevent XSS attacks)
- [x] 11.4.2 Validate CSRF protection on forms
- [x] 11.4.3 Test rate limiting (100 req/min per user)
- [x] 11.4.4 Test authentication system if enabled
- [x] 11.4.5 Record video tutorial (5-minute walkthrough)
- [x] 11.4.6 Create user guide for UI (navigation, filtering, export)
- [x] 11.4.7 Test accessibility (WCAG AA compliance, screen readers)
- [x] 11.4.8 Validate all tooltips and help text

---

## 12. Mathematical Validation & Calibration (25 tasks)

### 12.1 CES and Satiation Testing

- [x] 12.1.1 Unit test CES aggregation with known inputs
- [x] 12.1.2 Property test: CES monotonicity (more amenities → higher V_c)
- [x] 12.1.3 Test CES numerical stability (no overflow with large inputs)
- [x] 12.1.4 Test CES limits (ρ→0 Cobb-Douglas, ρ→1 linear)
- [x] 12.1.5 Unit test satiation curves with anchor points
- [x] 12.1.6 Property test: satiation asymptotes to 100
- [x] 12.1.7 Test satiation with extreme cases (V_c=0, V_c→∞)
- [x] 12.1.8 Validate κ_c computation from anchors (κ_c > 0)

### 12.2 Quality Scoring and Diversity

- [x] 12.2.1 Unit test Q_a components (size, popularity, brand, heritage)
- [x] 12.2.2 Test Q_a ranges (all scores in [0, 100])
- [x] 12.2.3 Test brand deduplication (verify weight reduction)
- [x] 12.2.4 Test opening hours bonus logic
- [x] 12.2.5 Unit test Shannon diversity index
- [x] 12.2.6 Test diversity with monoculture vs mixed categories
- [x] 12.2.7 Validate diversity bonus multiplier (1.0-1.2×)

### 12.3 Subscore Validation

- [x] 12.3.1 Validate all 7 subscores in [0, 100] range (EA, LCA, MUHAA, JEA, MORR, CTE, SOU)
- [x] 12.3.2 Validate subscore weights sum to 100
- [x] 12.3.3 Test each subscore with synthetic data (known outcomes)
- [x] 12.3.4 Property test: monotonicity (more access → higher scores)
- [x] 12.3.5 Test edge cases (zero amenities, unreachable locations)
- [x] 12.3.6 Validate no NaN or Inf values in any subscore
- [x] 12.3.7 Compare subscores across metros (sanity checks)

### 12.4 Parameter Calibration

- [x] 12.4.1 Calibrate ρ_c (CES elasticity) per category from expert judgment
- [x] 12.4.2 Calibrate κ_c (satiation) from anchor points (e.g., 5 groceries → 80%)
- [x] 12.4.3 Calibrate MORR component weights (C₁-C₅, default equal)
- [x] 12.4.4 Calibrate MUHAA hub mass weights (population, GDP, POI, culture)
- [x] 12.4.5 Conduct sensitivity analysis (vary parameters ±20%, measure output changes)
- [x] 12.4.6 Validate calibrated parameters with pilot test (Boulder County)
- [x] 12.4.7 Document calibration methodology and rationale
- [x] 12.4.8 Freeze parameters for v1.0 release
- [x] 12.4.9 Create parameter uncertainty documentation

---

## 13. Full Model Performance Testing (25 tasks)

### 13.1 Pipeline Benchmarking

- [x] 13.1.1 Benchmark full pipeline with all 7 subscores on pilot region (Boulder County)
- [x] 13.1.2 Measure time per subscore (EA, LCA, MUHAA, JEA, MORR, CTE, SOU)
- [x] 13.1.3 Identify bottleneck subscores (likely MUHAA, CTE with routing)
- [x] 13.1.4 Profile each subscore with cProfile or py-spy
- [x] 13.1.5 Measure peak memory usage per subscore
- [x] 13.1.6 Document resource requirements (CPU, RAM, disk I/O)

### 13.2 Full-Scale Testing

- [x] 13.2.1 Run full pipeline on all 3 states (CO/UT/ID, ~1M hexes)
- [x] 13.2.2 Monitor execution: logs, metrics, alerts
- [x] 13.2.3 Validate total run time <8 hours (target)
- [x] 13.2.4 Validate memory usage <16GB (target)
- [x] 13.2.5 Check temp disk usage (ensure <100GB)
- [x] 13.2.6 Validate all subscores computed for all hexes
- [x] 13.2.7 Run QA report on full outputs
- [x] 13.2.8 Generate summary statistics per metro

### 13.3 Performance Optimization

- [x] 13.3.1 Optimize MUHAA routing queries (cache common hub OD pairs)
- [x] 13.3.2 Optimize CTE path analysis (limit paths per hex)
- [x] 13.3.3 Parallelize subscore computation where possible (independent subscores)
- [x] 13.3.4 Use Polars or DuckDB for heavy aggregations
- [x] 13.3.5 Optimize Parquet I/O (compression, partitioning)
- [x] 13.3.6 Profile and optimize hot loops with Numba JIT
- [x] 13.3.7 Test optimizations (verify correctness, measure speedup)
- [x] 13.3.8 Document performance improvements achieved

### 13.4 UI Performance with Full Dataset

- [x] 13.4.1 Load full 1M hex dataset into UI
- [x] 13.4.2 Test viewport queries with 100K+ hexes visible
- [x] 13.4.3 Test zoom/pan performance (target <500ms)
- [x] 13.4.4 Test filter performance with full dataset
- [x] 13.4.5 Test choropleth rendering at all zoom levels
- [x] 13.4.6 Validate WebGL rendering with 1M hexes (via aggregation)
- [x] 13.4.7 Test UI memory usage in browser (<2GB)
- [x] 13.4.8 Optimize UI if needed (more aggressive aggregation)
- [x] 13.4.9 Load test UI with 10 concurrent users + full dataset

---

**Total Tasks:** 385 across 13 major workstreams (75 tasks added)
**Critical Path:** External Services (1.1-1.3) → Data Pipeline (2.1-2.3) → Integration Testing (3.1-3.3) → UI Deployment (11) → Full Model Testing (13)
**Estimated Timeline:** 8-10 weeks with dedicated team (expanded scope)
