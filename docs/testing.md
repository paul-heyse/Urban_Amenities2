# Testing & Coverage Guide

## Baseline coverage (current state)

The latest full run of `pytest --cov=src/Urban_Amenities2` yields 73.85% overall line coverage with substantial gaps in several
packages. Math kernels such as `ces` and `satiation` sit between 34%–64%, router modules remain around 68%–75%, and UI modules
like `callbacks`, `data_loader`, and `hex_selection` fall below 20%. I/O integrations for Overture, FAA, and NOAA also remain
under the new minimum thresholds (38%–65%).【2ad896†L1-L83】

These figures establish the baseline for the coverage enforcement work described below. Subsequent changes (`add-ui-coverage-
regressions`, `add-routing-coverage-regressions`, `add-math-coverage-regressions`) will be responsible for lifting the packages
to their target percentages.

## Running coverage locally

Use the default pytest configuration to exercise the suite with coverage instrumentation and strict thresholds:

```bash
pytest
```

The pytest configuration automatically expands to `pytest -q --strict-markers --strict-config --cov=src/Urban_Amenities2 \
    --cov-config=.coveragerc --cov-report=term-missing --cov-report=xml --cov-branch --cov-fail-under=95` so developers do not
need to remember the full command line. Coverage results are written to `coverage.xml` for downstream tooling and to the terminal
for immediate inspection.

Set `PYTEST_DISABLE_COVERAGE_CHECKS=1` when running exploratory tests without the package-level gate (for example, during tight
TDD loops). Remember to rerun the suite without the override before sending changes for review.

## Enforcement pipeline

* **Pytest gate** – A custom `pytest_sessionfinish` hook reads the package thresholds from `.coveragerc` and fails the run if
  `Urban_Amenities2.math` drops below 90%, `Urban_Amenities2.router` below 85%, `Urban_Amenities2.ui` below 85%, or
  `Urban_Amenities2.io` below 75%.【F:tests/conftest.py†L1-L39】【F:tests/conftest.py†L200-L243】
* **CI summary** – `scripts/check_coverage.py` parses `coverage.xml`, enforces the same thresholds during CI, and emits a JSON
  summary plus GitHub job annotations for traceability.【F:scripts/check_coverage.py†L1-L193】
* **Configuration** – `.coveragerc` declares the overall and per-package thresholds so local runs, the pytest hook, and CI share
  a single source of truth.【F:.coveragerc†L1-L17】

Follow this workflow to keep the suite above 95% overall line coverage while tracking minimum targets for the math, router, UI,
and I/O stacks.
