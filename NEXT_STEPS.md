# AUCS 2.0: What Remains After Implementation

## TL;DR - Critical Gaps

Your AI agents implemented all the code, but the system **cannot run** yet because:

1. ⚠️ **No routing engines deployed** - OSRM and OTP2 services don't exist
2. ⚠️ **No end-to-end test** - Never proven the full pipeline works
3. ⚠️ **Test failures** - test_cli.py has import errors
4. ℹ️ Missing operational infrastructure (monitoring, orchestration)
5. ℹ️ Need calibration and validation

**Good news:** ✅ **Stub audit found zero temporary implementations** - all code is production-quality (see `STUB_AUDIT_REPORT.md`)

**Bottom line:** You have ~80% of a complete system. The remaining 20% is deployment, testing, and operations.

---

## What You Have ✅

- **Complete implementation** of all AUCS 2.0 algorithms (E1-E39)
- **Proper architecture** (hexagonal, functional core, schema-first)
- **600+ parameters** managed via Pydantic
- **CLI interface** for all pipeline stages
- **25+ unit/integration tests**
- **Data ingestion** for all sources (Overture, GTFS, climate, parks, jobs)
- **7 subscore implementations** (EA as template for others)
- **Documentation** (comprehensive specs, guides, conventions)

---

## What You Need (Priority Order)

### P0 - Blocking (Must Fix to Run)

#### 1. Deploy External Services

**Why blocking:** The code calls OSRM and OTP2 APIs, but those services don't exist.

**What to do:**

```bash
# Deploy OSRM (car/bike/foot routing)
# Option 1: Quick Docker setup
docker run -d -p 5000:5000 --name osrm-car \
  -v $(pwd)/osrm-data:/data \
  osrm/osrm-backend osrm-routed /data/car.osrm

docker run -d -p 5001:5000 --name osrm-bike \
  -v $(pwd)/osrm-data:/data \
  osrm/osrm-backend osrm-routed /data/bike.osrm

docker run -d -p 5002:5000 --name osrm-foot \
  -v $(pwd)/osrm-data:/data \
  osrm/osrm-backend osrm-routed /data/foot.osrm

# Deploy OTP2 (transit routing)
docker run -d -p 8080:8080 --name otp2 \
  -v $(pwd)/otp-data:/var/otp \
  opentripplanner/opentripplanner:2.5 --load /var/otp
```

**But first you need to build the graphs:**

- OSRM: Extract Overture Transportation → OSM format → run osrm-extract/contract
- OTP2: Collect GTFS feeds + Overture streets → run graph build

**Estimated time:** 2-3 days (including data prep)

#### 2. Fix Test Failures

```bash
# Current status
pytest  # Fails with import error in test_cli.py

# Fix the import issue, then run
pytest -v
```

**Estimated time:** 1-2 hours

#### 3. Create End-to-End Integration Test

**Critical missing piece:** No test has ever run the full pipeline.

**Create:** `tests/test_e2e_boulder.py`

- Use real data for Boulder, CO (~1000 hexes)
- Run: ingest → route → compute → score → aggregate
- Validate outputs exist and pass schema checks

**Estimated time:** 2-3 days

---

### P1 - High Value (Should Do)

#### 4. Expand Test Coverage

Current: ~13 test files, unknown coverage
Target: 70%+ for core math, 60%+ for I/O

```bash
pytest --cov=src/Urban_Amenities2 --cov-report=html
open htmlcov/index.html
```

Focus on:

- Routing integration tests (mock OSRM/OTP)
- Data ingestion tests (category crosswalk, deduplication)
- Mathematical property tests (hypothesis)

**Estimated time:** 1 week

#### 5. Set Up Basic Monitoring

- Structured logging (already have structlog, just configure it)
- Pipeline execution metrics
- Data quality dashboards
- Alert on failures

**Estimated time:** 3-4 days

#### 6. Create Deployment Documentation

- How to set up OSRM and OTP2
- How to run the pipeline
- How to update data
- Troubleshooting guide

**Estimated time:** 2-3 days

#### 7. Parameter Calibration

- Run sensitivity analysis on key parameters
- Validate outputs against known good areas
- Adjust parameters if needed
- Document changes

**Estimated time:** 1 week

---

### P2 - Nice to Have (Future)

#### 8. Query API (Optional)

If you want to query results interactively:

```python
# FastAPI + DuckDB = instant API over Parquet files
@app.get("/aucs/hex/{hex_id}")
def get_score(hex_id: str):
    return duckdb.query(
        "SELECT * FROM 'output/aucs.parquet' WHERE hex_id = ?",
        [hex_id]
    ).fetchone()
```

**Estimated time:** 3-5 days

#### 9. Orchestration (Automated Updates)

Use Prefect or Airflow for scheduled data updates.

**Estimated time:** 1 week

#### 10. Performance Optimization

Profile and optimize bottlenecks.

**Estimated time:** 1 week

---

## Recommended Plan

### Week 1-2: Make It Work

1. ✅ Fix test_cli.py
2. ✅ Deploy OSRM and OTP2 (Docker is fine)
3. ✅ Run end-to-end test on Boulder data
4. ✅ Fix any blocking bugs

**Deliverable:** Pipeline runs successfully start to finish.

### Week 3-4: Make It Right

5. ✅ Expand test coverage
6. ✅ Add data quality checks
7. ✅ Set up monitoring
8. ✅ Calibrate parameters
9. ✅ Validate outputs

**Deliverable:** High confidence in quality and reliability.

### Week 5-6: Make It Production

10. ✅ Performance optimization
11. ✅ Deployment documentation
12. ✅ Backup/recovery procedures
13. ✅ (Optional) Deploy query API

**Deliverable:** Production-ready system.

---

## Decision Points

### 1. Deployment Target

**Question:** Where will this run?

- Local development machine (easiest)
- Cloud VMs (AWS/GCP/Azure)
- Kubernetes cluster
- Serverless functions

**Recommendation:** Start with Docker on a single VM, scale later if needed.

### 2. Update Frequency

**Question:** How often do you need to update scores?

- Real-time (requires API + incremental updates)
- Daily (requires orchestration)
- Weekly (can be manual or scheduled)
- Quarterly (manual is fine)

**Recommendation:** Start with quarterly manual updates, automate later.

### 3. Access Pattern

**Question:** How will users access results?

- File downloads (simplest)
- Query API (more flexible)
- Dashboard/web app (user-friendly)
- Embedded in other systems

**Recommendation:** Start with file downloads (GeoJSON, Parquet, CSV), add API if needed.

### 4. API Requirement

**Question:** Do you need a query API?

**If YES:**

- Users need to query by address/location
- Real-time scoring updates
- Integration with other applications
→ **Implement FastAPI + DuckDB** (~3-5 days)

**If NO:**

- Batch processing is sufficient
- Users work with files
- Updates are infrequent
→ **Skip API, focus on pipeline reliability**

---

## Quick Start (Right Now)

```bash
cd /home/paul/Urban_Amenities2

# 1. Fix tests
pytest -v  # See what's broken
# Fix test_cli.py import error

# 2. Check what's actually implemented
find src/Urban_Amenities2 -name "*.py" | head -20
pytest --collect-only

# 3. Review production readiness checklist
cat PRODUCTION_READINESS_CHECKLIST.md

# 4. Set up external services (see section 2 in checklist)
# Start with Docker containers for OSRM and OTP2

# 5. Create Boulder test dataset
# Download Overture data for Boulder bbox
# Download RTD GTFS for relevant routes
# Create tests/test_e2e_boulder.py

# 6. Run end-to-end test
pytest tests/test_e2e_boulder.py -v
```

---

## Files to Read

1. **PRODUCTION_READINESS_CHECKLIST.md** - Comprehensive 7-area breakdown
2. **openspec/IMPLEMENTATION_GUIDE.md** - Architecture and change proposals
3. **openspec/project.md** - Project conventions and constraints
4. **AGENTS.md** - Repository guidelines

---

## Summary

**Status:** Implementation complete (~80%), operations needed (~20%)

**Critical path:**

1. Deploy OSRM + OTP2 (2-3 days) ← **START HERE**
2. Fix tests + create e2e test (3-4 days)
3. Validation + calibration (1 week)
4. Documentation + deployment (1 week)

**Total time to production:** 6-8 weeks with deliberate, tested deployment

**Key risk:** External routing services are not optional—the system cannot run without them.

**Good news:** The hard part (implementation) is done. What remains is deployment engineering, which is well-understood and systematic.
