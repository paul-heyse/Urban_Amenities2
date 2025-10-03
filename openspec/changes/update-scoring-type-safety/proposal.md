## Why
Core scoring pipelines (corridor enrichment, seasonal outdoors, hub/airport access, essentials, quality scoring) contribute 32 mypy errors due to ambiguous pandas operations, shapely geometry handling, and NumPy helper functions returning `Any`. These areas underpin AUCS subscores; leaving them loosely typed risks numerical regressions and blocks the broader type-safety push.

## What Changes
- Apply `numpy.typing` and typed pandas operations to corridor/seasonal/hub score modules, ensuring shapely geometries and aggregations expose precise types.
- Refactor quality/dedupe helpers (`quality/dedupe.py`, `dedupe/pois.py`) and `math/ces.py` to return typed `NDArray` objects and handle offsets without implicit `Any`.
- Update quality scoring routines to use typed loc/index operations and avoid ambiguous Series unions.
- Expand regression tests (or property tests) to confirm calculations remain stable after typing refactors.

## Impact
- Affected specs: `qa/scoring-type-safety`
- Affected code: `scores/corridor_*`, `scores/seasonal_outdoors.py`, `scores/hub_airport_access.py`, `scores/essentials_access.py`, `scores/leisure_culture_access.py`, `quality/dedupe.py`, `dedupe/pois.py`, `math/ces.py`, `quality/scoring.py` and supporting tests.
