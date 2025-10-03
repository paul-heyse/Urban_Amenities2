## 1. Scoring pipeline typing
- [ ] 1.1 Introduce `numpy.typing.NDArray` helpers for corridor/seasonal scoring math (`math/ces.py`, `quality/dedupe.py`, `dedupe/pois.py`).
- [ ] 1.2 Rework corridor enrichment + seasonal outdoors to operate on typed DataFrames/Series and shapely geometries with explicit return types.
- [ ] 1.3 Resolve hub/airport and essentials access typing (slots, config constructors, dictionary lookups) to satisfy mypy.
- [ ] 1.4 Update quality scoring selectors to avoid ambiguous unions and ensure typed returns.
- [ ] 1.5 Add targeted tests (unit/property) verifying typed refactors keep numeric outputs stable.
- [ ] 1.6 Run `mypy src/Urban_Amenities2/scores src/Urban_Amenities2/quality src/Urban_Amenities2/dedupe src/Urban_Amenities2/math --warn-unused-ignores` and document new typing patterns.
