## ADDED Requirements
### Requirement: Scoring Pipeline Type Safety
AUCS scoring modules SHALL expose typed math helpers and pandas/shapely operations so subscores are validated statically.

#### Scenario: Typed scoring computations
- **WHEN** `mypy src/Urban_Amenities2/scores --warn-unused-ignores` is executed
- **THEN** corridor, seasonal, hub/airport, essentials, and leisure scoring modules SHALL pass without implicit `Any` returns or union misuses.

#### Scenario: Typed math + dedupe helpers
- **WHEN** math utilities (`math/ces.py`, `quality/dedupe.py`, `dedupe/pois.py`) are type checked
- **THEN** all helper functions SHALL return `NDArray` or appropriate numeric scalars, and vectorised operations SHALL not rely on `Any` coercion.

#### Scenario: Quality scoring selectors
- **WHEN** quality scoring aggregates category data
- **THEN** typed Series/DataFrame selectors SHALL be used so mypy validates without overload warnings.
