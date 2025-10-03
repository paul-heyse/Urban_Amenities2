## 1. Baseline Assessment
- [x] 1.1 Generate current line/branch coverage report (pytest --cov, coverage html)
      - 2025-10-03 baseline: 69% line / 0% branch coverage with ~1,545 missed statements across UI, routing, ingestion, and scoring modules.
- [x] 1.2 Catalogue uncovered modules/functions; prioritise by risk and execution frequency
      - Highest risk gaps: `ui.callbacks`, `ui.data_loader`, `router.osrm`, `quality.scoring`, `io.enrichment.*`, and `scores.essentials_access` due to production critical paths and heavy branching.
      - Secondary priorities: `cache.manager` error paths, `ui.parameters` adjustments, and `ui/layouts` factories used in Dash shell.
- [x] 1.3 Identify test gaps requiring fixtures, mocks, or architectural seams
      - Added plan to introduce reusable Dash/UI dataset fixture, cache manager harness, and HTTP client stubs for OSRM/OTP to decouple network calls.
      - Flagged need for manifest/versioning seam to test snapshot invalidation separately from disk I/O.

## 2. Test Infrastructure Enhancements
- [x] 2.1 Add reusable fixtures for ingestion datasets, routing clients, cache backends, and UI contexts
      - `tests/conftest.py` now provisions cached hex datasets, `CacheManager` fixture, Dash `UISettings`, and synthetic overlays reused by UI/layout tests.
- [x] 2.2 Introduce service stubs/mocks (OSRM, OTP, external APIs) to enable deterministic integration tests
      - Added shared `StubSession` with OSRM/OTP fixtures; updated routing tests to consume these deterministic clients.
- [ ] 2.3 Update CI workflow to capture coverage artifacts and enforce ≥95% line / ≥90% branch thresholds
- [x] 2.4 Document coverage expectations in CONTRIBUTING.md and developer guides

## 3. Module-Specific Coverage Improvements
- [ ] 3.1 Data ingestion: add scenario tests for each source adapter with edge cases (missing data, malformed records)
- [ ] 3.2 Routing: cover batch matrix generation, error handling, and fallback logic
- [ ] 3.3 Scoring: expand property-based tests for CES, satiation, logsum, and subscore calculators
- [ ] 3.4 Caching & versioning: exercise TTL logic, invalidation, manifest workflows
      - Progress: new cache manager tests cover TTL selection, key hashing, invalidation, and error handling; versioning manifest coverage still pending.
- [x] 3.5 UI & CLI: implement Dash callback tests, CLI command smoke tests, export permutations
      - Added structural tests for UI components, filters, overlay controls, layouts, and parameter adjuster behaviour.

## 4. Quality Gates & Regression Protection
- [ ] 4.1 Add mutation testing or fuzz hooks for critical math kernels (stretch goal)
- [ ] 4.2 Integrate coverage diff reporting into PR template/dashboard
- [ ] 4.3 Establish monitoring to track coverage trend per release

## 5. Validation & Sign-off
- [ ] 5.1 Run full pytest suite with coverage; confirm targets met
- [ ] 5.2 Review documentation updates and onboarding materials
- [ ] 5.3 Obtain stakeholder approval; archive change upon completion
