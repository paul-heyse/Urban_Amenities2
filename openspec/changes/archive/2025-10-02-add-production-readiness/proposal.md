# Production Readiness for AUCS 2.0

## Why

All AUCS 2.0 implementation tasks are complete, but the system cannot run in production without:

1. **External services** (OSRM, OTP2) - currently no routing engines deployed
2. **End-to-end validation** - no proof the full pipeline works on real data
3. **Operational infrastructure** - no monitoring, orchestration, or recovery procedures
4. **Comprehensive testing** - test_cli.py has import errors; missing integration tests
5. **Deployment procedures** - no documented way to deploy and maintain the system

Without these, the codebase is a collection of modules but not a functioning application.

## What Changes

**External Service Deployment:**

- Deploy OSRM services (car, bike, foot) with Overture-based graphs
- Deploy OTP2 service with GTFS + street networks
- Create service health checks and monitoring
- Document rebuild procedures

**Testing & Validation:**

- Fix test_cli.py import error (blocking)
- Create end-to-end integration test with real Boulder, CO data
- Expand test coverage to 70%+ for core modules
- Add data quality validation tests
- Create smoke test suite for CI/CD

**Operational Infrastructure:**

- Set up data pipeline orchestration (Prefect or Airflow)
- Implement centralized logging and metrics
- Create backup and recovery procedures
- Add alerting for failures

**Documentation:**

- Deployment guide (OSRM/OTP2 setup)
- Operations manual (data updates, troubleshooting)
- API documentation (if API layer added)
- User guide for interpreting results

**Optional Query API:**

- FastAPI application for querying results
- DuckDB-based query layer over Parquet files
- OpenAPI/Swagger documentation
- Rate limiting and authentication

**Calibration & Validation:**

- Parameter sensitivity analysis
- Cross-validation with external benchmarks
- Performance profiling and optimization

**NEW: Interactive UI Deployment:**

- Deploy Dash application server (Gunicorn/Uvicorn with multi-workers)
- Configure web server (Nginx reverse proxy, SSL, HTTPS)
- Set up caching layer (DiskCache or Redis for API responses)
- Test UI responsiveness (desktop, tablet, mobile)
- Browser compatibility testing (Chrome, Firefox, Safari)
- UI load testing (10+ concurrent users)
- WebGL rendering validation for heat maps
- Shareable URL testing
- UI-specific security testing (XSS, CSRF, rate limiting)
- UI documentation and video tutorial

**NEW: Mathematical Validation:**

- Unit tests for all new math kernels (CES, satiation, diversity, Q_a)
- Property-based tests for mathematical invariants
- Validate all subscores in [0, 100] range
- Cross-subscore consistency (weights sum to 100)
- Numerical stability testing (avoid overflow, NaN)
- Calibrate CES elasticity (ρ_c) per category
- Calibrate satiation kappa (κ_c) from anchor points
- Calibrate component weights for MORR, MUHAA

**NEW: Full Model Performance:**

- Benchmark complete pipeline with all 7 subscores
- Measure incremental time per subscore (identify bottlenecks)
- Optimize expensive computations (MUHAA routing, CTE path analysis)
- Test with full 1M hex dataset (CO/UT/ID)
- Validate memory usage <16GB
- Target: <8 hours for full 3-state run
- Profile and optimize UI with full dataset

## Impact

- Affected specs: `testing`, `deployment`, `operations` (all new)
- Affected code:
  - New: `deployment/`, `monitoring/`, `api/` (if API added), `ui/` (Dash application)
  - Modified: Fix tests/, add CI/CD configuration, add UI tests
  - Enhanced: All 7 subscore modules require validation and calibration
- External dependencies:
  - OSRM Docker containers or dedicated servers
  - OTP2 Java application
  - Orchestration platform (Prefect/Airflow optional)
  - Web server (Nginx) for UI
  - Cache backend (DiskCache or Redis)
  - New data sources: GBFS, BEA GDP, CBSA boundaries, FAA enplanements
- **BREAKING**: System cannot run without OSRM and OTP2 services
- **NEW SCOPE**: Adds UI deployment (25 tasks), mathematical validation (25 tasks), full model testing (25 tasks)
- Timeline: 8-10 weeks for full production readiness (expanded from 6-8 weeks)
