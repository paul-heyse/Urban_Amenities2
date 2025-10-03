## 1. Baseline Assessment
- [ ] 1.1 Generate current line/branch coverage report (pytest --cov, coverage html)
- [ ] 1.2 Catalogue uncovered modules/functions; prioritise by risk and execution frequency
- [ ] 1.3 Identify test gaps requiring fixtures, mocks, or architectural seams

## 2. Test Infrastructure Enhancements
- [ ] 2.1 Add reusable fixtures for ingestion datasets, routing clients, cache backends, and UI contexts
- [ ] 2.2 Introduce service stubs/mocks (OSRM, OTP, external APIs) to enable deterministic integration tests
- [ ] 2.3 Update CI workflow to capture coverage artifacts and enforce ≥95% line / ≥90% branch thresholds
- [ ] 2.4 Document coverage expectations in CONTRIBUTING.md and developer guides

## 3. Module-Specific Coverage Improvements
- [ ] 3.1 Data ingestion: add scenario tests for each source adapter with edge cases (missing data, malformed records)
- [ ] 3.2 Routing: cover batch matrix generation, error handling, and fallback logic
- [ ] 3.3 Scoring: expand property-based tests for CES, satiation, logsum, and subscore calculators
- [ ] 3.4 Caching & versioning: exercise TTL logic, invalidation, manifest workflows
- [ ] 3.5 UI & CLI: implement Dash callback tests, CLI command smoke tests, export permutations

## 4. Quality Gates & Regression Protection
- [ ] 4.1 Add mutation testing or fuzz hooks for critical math kernels (stretch goal)
- [ ] 4.2 Integrate coverage diff reporting into PR template/dashboard
- [ ] 4.3 Establish monitoring to track coverage trend per release

## 5. Validation & Sign-off
- [ ] 5.1 Run full pytest suite with coverage; confirm targets met
- [ ] 5.2 Review documentation updates and onboarding materials
- [ ] 5.3 Obtain stakeholder approval; archive change upon completion
