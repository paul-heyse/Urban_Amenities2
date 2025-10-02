# AUCS 2.0 Production Readiness Checklist

## Current Status

✅ **Core implementation complete** (all OpenSpec tasks implemented by AI agents)
✅ **Basic tests present** (25 test cases across unit/integration)
⚠️ **Tests have import errors** (test_cli.py needs fixing)

## What Remains: 7 Critical Areas

---

## 1. 🧪 Testing & Quality Assurance (CRITICAL)

### 1.1 Fix Existing Test Issues

- [ ] **Fix test_cli.py import error** (blocking test suite)
- [ ] Run full test suite: `pytest -v`
- [ ] Fix any failing tests
- [ ] Ensure all tests pass consistently

### 1.2 Expand Test Coverage

**Current:** ~13 test files
**Target:** 80%+ coverage for core modules, 60%+ for I/O

**Priority Test Additions:**

- [ ] **Routing integration tests**
  - Mock OSRM and OTP2 responses
  - Test error handling (service down, invalid responses)
  - Test batching and caching logic

- [ ] **Data ingestion tests**
  - Test Overture Places parsing with real sample data
  - Test GTFS parsing with fixture feeds
  - Test category crosswalk with edge cases
  - Test POI deduplication logic

- [ ] **End-to-End integration test**
  - Small synthetic dataset (10 hexes, 50 POIs, 1 transit route)
  - Run entire pipeline from ingestion → final AUCS scores
  - Verify output schemas and score ranges
  - **This is the most critical missing test**

- [ ] **Mathematical property tests** (hypothesis)
  - Test GTC monotonicity (higher travel time → higher cost)
  - Test logsum properties (IIA violations, substitution)
  - Test CES homogeneity
  - Test satiation asymptotic behavior

- [ ] **Data quality tests**
  - Test Pandera schema validation on real data samples
  - Test handling of missing/malformed data
  - Test hex resolution consistency

**Commands:**

```bash
pytest -v --cov=src/Urban_Amenities2 --cov-report=html
pytest -v tests/test_integration_pipeline.py  # Critical test
```

---

## 2. 🚀 External Service Deployment (BLOCKING)

### 2.1 OSRM Deployment

The system **cannot run** without OSRM for car/bike/foot routing.

**Setup Required:**

- [ ] **Build OSRM graphs from Overture Transportation data**
  - Download Overture Transportation for CO/UT/ID
  - Extract road network to OSM PBF format
  - Run `osrm-extract` for car, bike, foot profiles
  - Run `osrm-contract` to prepare routing graphs

- [ ] **Deploy OSRM services**
  - Option A: Docker containers (recommended for dev/test)

    ```bash
    docker run -p 5000:5000 -v ./osrm-data:/data osrm/osrm-backend osrm-routed /data/car.osrm
    docker run -p 5001:5000 -v ./osrm-data:/data osrm/osrm-backend osrm-routed /data/bike.osrm
    docker run -p 5002:5000 -v ./osrm-data:/data osrm/osrm-backend osrm-routed /data/foot.osrm
    ```

  - Option B: Dedicated servers for production

- [ ] **Configure routing client**
  - Update config/routing.yml with OSRM endpoints
  - Test connectivity: `curl http://localhost:5000/route/v1/driving/-104.9903,39.7392;-104.9903,39.7492`

- [ ] **Create OSRM update pipeline**
  - Schedule quarterly rebuilds (when Overture updates)
  - Document rebuild procedure

### 2.2 OTP2 Deployment

Required for transit routing.

**Setup Required:**

- [ ] **Build OTP2 graph**
  - Gather all GTFS feeds for CO/UT/ID (from data ingestion)
  - Get Overture streets for pedestrian network
  - Optional: Add elevation data (SRTM/NED)
  - Run OTP2 graph build: `java -Xmx8G -jar otp.jar --build --save /data/graphs/co-ut-id`

- [ ] **Deploy OTP2 server**
  - Option A: Docker

    ```bash
    docker run -p 8080:8080 -v ./otp-data:/var/otp opentripplanner/opentripplanner:2.5 --load /var/otp
    ```

  - Option B: Java application on server

- [ ] **Configure OTP client**
  - Update config with OTP GraphQL endpoint
  - Test: `curl http://localhost:8080/otp/routers/default/transmodel/index/graphql -d '{"query":"{feeds{feedId}}"}}'`

- [ ] **Create OTP update pipeline**
  - Weekly GTFS updates (automated download + graph rebuild)
  - Document rebuild procedure

### 2.3 Service Health Monitoring

- [ ] **Implement health checks**
  - OSRM: periodic `/route` test queries
  - OTP: periodic GraphQL queries
  - Alert on failures

- [ ] **Document service requirements**
  - Memory: OSRM ~2GB per profile, OTP ~8GB per graph
  - CPU: Recommend 4+ cores for production
  - Storage: ~10GB for OSRM data, ~20GB for OTP graphs

---

## 3. 🔌 API Layer (Optional but Recommended)

Currently, the system is a **batch pipeline** (CLI-driven). For a fully functioning application, consider adding a **REST/GraphQL API** for querying results.

### Option A: Simple File-Based API (Minimal)

If you only need occasional queries:

- [ ] Export final AUCS scores to formats:
  - GeoJSON (for QGIS, web maps)
  - Parquet (for analytics tools)
  - CSV (for Excel)
- [ ] Create S3/cloud storage for outputs
- [ ] Document file access patterns

### Option B: Query API (Recommended)

For interactive queries (e.g., "show me AUCS for this address"):

**Tech Stack:** FastAPI + DuckDB (query Parquet files)

- [ ] **Create FastAPI application**
  - `src/Urban_Amenities2/api/main.py`
  - Endpoints:
    - `GET /aucs/hex/{hex_id}` - Get score for specific hex
    - `GET /aucs/location?lat={lat}&lon={lon}` - Get score for lat/lon
    - `GET /aucs/bbox?minlat=&maxlat=&minlon=&maxlon=` - Get scores in bounding box
    - `GET /aucs/compare?hex1={h1}&hex2={h2}` - Compare two locations
    - `GET /explainability/{hex_id}` - Get top contributors

- [ ] **Implement query layer**
  - Use DuckDB to query Parquet files (no database needed!)
  - Add caching layer (Redis or in-memory)
  - Add rate limiting

- [ ] **Add API documentation**
  - FastAPI auto-generates OpenAPI/Swagger docs
  - Add usage examples

- [ ] **Deploy API**
  - Docker container or cloud function
  - Add authentication if needed

**Example implementation:**

```python
from fastapi import FastAPI
import duckdb

app = FastAPI()

@app.get("/aucs/hex/{hex_id}")
def get_aucs_by_hex(hex_id: str):
    conn = duckdb.connect()
    result = conn.execute(
        "SELECT * FROM 'output/aucs.parquet' WHERE hex_id = ?",
        [hex_id]
    ).fetchone()
    return {"hex_id": hex_id, "aucs": result[1], "subscores": {...}}
```

---

## 4. 📊 End-to-End Integration & Validation

### 4.1 Full Pipeline Integration Test

**Most Critical Missing Piece**

Create a complete end-to-end test with real (but small) data:

- [ ] **Prepare test dataset**
  - Select 1 small city (e.g., Boulder, CO)
  - ~1000 hexes
  - Real Overture POIs (100-500)
  - 1-2 transit routes from GTFS
  - Real climate data for the area

- [ ] **Run full pipeline**

  ```bash
  # 1. Ingest data
  aucs ingest overture-places --bbox 40.0,-105.3,40.1,-105.2
  aucs ingest gtfs --agency RTD --routes 205,206
  aucs ingest climate --state CO

  # 2. Build routing (mock/test mode)
  aucs routing build-osrm --test-mode

  # 3. Compute accessibility
  aucs compute accessibility --market boulder-test

  # 4. Compute subscores
  aucs score ea --market boulder-test
  aucs score lca --market boulder-test
  # ... other subscores

  # 5. Aggregate
  aucs aggregate --market boulder-test

  # 6. Validate outputs
  aucs validate-outputs --market boulder-test
  ```

- [ ] **Validate outputs**
  - Check output files exist
  - Check schema compliance (Pandera)
  - Check score ranges (0-100)
  - Check distribution (not all zeros/hundreds)
  - Spot-check: high scores near downtown, transit

- [ ] **Performance benchmarking**
  - Time each pipeline stage
  - Memory profiling
  - Identify bottlenecks

- [ ] **Create smoke test suite**
  - Automated test that runs on CI/CD
  - Uses the Boulder test dataset
  - Runs in <30 minutes

### 4.2 Cross-Validation

- [ ] **Face validity checks**
  - Compare AUCS with known good areas
  - Denver downtown should score high
  - Rural areas should score lower
  - Transit-rich areas should have high MORR

- [ ] **Correlation checks**
  - Compare with external data (if available)
    - Walk Score (if accessible)
    - Census ACS accessibility variables
    - Housing prices (should correlate positively)

- [ ] **Edge case testing**
  - Hexes with zero POIs
  - Hexes with no transit
  - Hexes in mountains (sparse data)
  - Hexes at state borders

---

## 5. 🔧 Operational Infrastructure

### 5.1 Data Pipeline Orchestration

Currently manual; needs automation for production.

- [ ] **Choose orchestrator**
  - Option A: Prefect (recommended, modern, Python-native)
  - Option B: Apache Airflow (enterprise-grade)
  - Option C: Cron + shell scripts (simplest)

- [ ] **Create data update workflows**
  - Daily: GTFS-RT for reliability metrics
  - Weekly: GTFS static updates
  - Quarterly: Overture Places/Transportation updates
  - Annual: LODES jobs, schools data

- [ ] **Implement error handling**
  - Retry logic for API failures
  - Alert on pipeline failures
  - Rollback capability

- [ ] **Create monitoring dashboard**
  - Track pipeline execution times
  - Monitor data freshness
  - Alert on stale data

### 5.2 Logging & Monitoring

- [ ] **Centralize logs**
  - Already using structlog (good!)
  - Ship logs to centralized system (CloudWatch, Datadog, etc.)
  - Add log retention policy

- [ ] **Add metrics**
  - Pipeline execution times
  - Data quality metrics (POI counts, coverage)
  - API latency (if API exists)
  - OSRM/OTP health

- [ ] **Set up alerts**
  - Pipeline failures
  - Data quality degradation
  - External service downtime
  - Disk space warnings

### 5.3 Backup & Recovery

- [ ] **Data backup strategy**
  - Version all input data (S3 versioning or snapshots)
  - Back up intermediate Parquet files
  - Back up final outputs

- [ ] **Disaster recovery plan**
  - Document how to rebuild from backups
  - Document OSRM/OTP graph rebuild
  - Test recovery procedure

- [ ] **Version control for outputs**
  - Tag each scoring run with version
  - Keep last N versions accessible
  - Document what changed between versions

---

## 6. 📖 Documentation & Training

### 6.1 User Documentation

- [ ] **API documentation** (if API exists)
  - Endpoint reference
  - Authentication guide
  - Rate limits
  - Example queries

- [ ] **Data documentation**
  - Output schema reference
  - Interpretation guide (what does AUCS mean?)
  - Methodology summary (for non-technical users)
  - Limitations and caveats

- [ ] **User guides**
  - How to query scores for an address
  - How to interpret subscores
  - How to visualize results
  - FAQ

### 6.2 Operational Documentation

- [ ] **Deployment guide**
  - OSRM setup instructions
  - OTP setup instructions
  - Infrastructure requirements
  - Cost estimates

- [ ] **Maintenance guide**
  - Data update procedures
  - Graph rebuild procedures
  - Troubleshooting common issues
  - Performance tuning

- [ ] **Developer guide**
  - Architecture overview (already have this!)
  - How to add new subscores
  - How to modify parameters
  - Testing guidelines

### 6.3 Training Materials

- [ ] **Internal training**
  - For ops team (how to run/monitor)
  - For support team (how to interpret results)

- [ ] **External materials** (if public-facing)
  - Video walkthrough
  - Case studies
  - Webinar/presentation

---

## 7. 🎯 Calibration & Fine-Tuning

### 7.1 Parameter Calibration

The default parameters from the spec may need adjustment for your specific markets.

- [ ] **Run sensitivity analysis**
  - Use calibration utilities (already implemented in EA)
  - Vary key parameters:
    - Mode decay half-lives (t_1/2)
    - Transfer penalties
    - CES elasticities (ρ_c)
    - Satiation parameters (κ_c)
  - Document impact on scores

- [ ] **Validate against ground truth** (if available)
  - Survey data on perceived accessibility
  - Expert judgment on known good/bad areas
  - External datasets (Walk Score, etc.)

- [ ] **Adjust parameters**
  - Update configs/params.yml
  - Document rationale
  - Re-run scoring
  - Compare before/after

- [ ] **Cross-metro consistency**
  - Compare CO vs UT vs ID distributions
  - Ensure fair comparisons
  - Consider anchor-based normalization

### 7.2 Performance Optimization

After validation, optimize for production speed.

- [ ] **Profile bottlenecks**

  ```bash
  python -m cProfile -o profile.stats -m Urban_Amenities2.cli run-full-pipeline
  snakeviz profile.stats
  ```

- [ ] **Optimize hot paths**
  - Add Numba JIT where missing
  - Vectorize remaining loops
  - Use Polars/DuckDB for large joins

- [ ] **Parallelize where possible**
  - State-level parallelization (CO, UT, ID separately)
  - Hex chunking for accessibility matrices
  - Use Dask/Ray for massive matrices

- [ ] **Optimize I/O**
  - Use Parquet partitioning by state/metro
  - Enable Parquet compression
  - Use columnar reads (only read needed columns)

---

## Phased Rollout Plan

### Phase 1: Make It Work (Week 1-2)

1. ✅ Fix test_cli.py import error
2. ✅ Deploy OSRM and OTP2 (even local Docker is fine)
3. ✅ Run end-to-end integration test on Boulder test data
4. ✅ Fix any blocking bugs

**Deliverable:** Pipeline runs successfully from start to finish on test data.

### Phase 2: Make It Right (Week 3-4)

5. ✅ Expand test coverage to 70%+
6. ✅ Add comprehensive data quality checks
7. ✅ Add monitoring and logging
8. ✅ Calibrate parameters on test markets
9. ✅ Validate outputs against external benchmarks

**Deliverable:** High confidence in result quality and system reliability.

### Phase 3: Make It Fast (Week 5-6)

10. ✅ Performance profiling and optimization
11. ✅ Parallelize heavy computations
12. ✅ Set up data pipeline orchestration
13. ✅ Add caching layers

**Deliverable:** Full-state scoring runs in acceptable time (<6 hours target).

### Phase 4: Make It Production (Week 7-8)

14. ✅ Deploy to production infrastructure
15. ✅ Set up monitoring and alerting
16. ✅ Create backup/recovery procedures
17. ✅ Write operational documentation
18. ✅ (Optional) Deploy query API

**Deliverable:** Production-ready system with operational procedures.

---

## Quick Priority Matrix

### Must Have (P0 - Blocking)

- ⚠️ Fix test_cli.py import error
- ⚠️ Deploy OSRM services
- ⚠️ Deploy OTP2 service
- ⚠️ End-to-end integration test
- ⚠️ Output validation checks

### Should Have (P1 - High Value)

- Expand test coverage (70%+)
- Data quality validation
- Parameter calibration
- Basic monitoring/logging
- Operational documentation

### Nice to Have (P2 - Future Enhancement)

- Query API
- Advanced monitoring dashboard
- Performance optimization
- Automated orchestration (Prefect/Airflow)
- Cross-validation with external data

---

## Success Criteria

The system is "production-ready" when:

1. ✅ **All tests pass** with 70%+ coverage
2. ✅ **End-to-end test succeeds** on real data
3. ✅ **External services deployed** (OSRM, OTP2)
4. ✅ **Output validation passes** (schemas, ranges, sanity checks)
5. ✅ **Performance acceptable** (<6 hours for full state)
6. ✅ **Monitoring in place** (logs, metrics, alerts)
7. ✅ **Documentation complete** (operational procedures)
8. ✅ **Backup/recovery tested**

---

## Next Immediate Steps

**Start here (in order):**

```bash
# 1. Fix tests
cd /home/paul/Urban_Amenities2
pytest -v  # Identify what's broken

# 2. Deploy external services (Docker for now)
# Follow OSRM/OTP2 setup in section 2

# 3. Create integration test
# Create tests/test_e2e_boulder.py

# 4. Run pipeline on test data
aucs run full-pipeline --market boulder-test --validate

# 5. Validate outputs
ls output/
aucs validate-outputs output/aucs.parquet
```

**Questions to answer:**

1. What's your deployment target? (local, cloud, hybrid)
2. Do you need a query API or just batch outputs?
3. What's your update cadence? (daily, weekly, quarterly)
4. Who are the end users? (internal analysts, public API, etc.)

---

## Summary

**What you have:** Solid implementation of the AUCS model with proper architecture.

**What you need:**

1. **Testing** - Fix import errors, add e2e tests, expand coverage
2. **External Services** - Deploy OSRM and OTP2 (blocking!)
3. **Integration** - Prove the full pipeline works end-to-end
4. **Operations** - Monitoring, logging, orchestration
5. **Documentation** - User guides, ops procedures
6. **Calibration** - Validate and tune parameters
7. **(Optional) API** - If you need queryable access to results

The implementation is ~80% complete. The remaining 20% is **operational readiness**, which is critical but often underestimated. Follow the phased rollout plan above to systematically address each area.
