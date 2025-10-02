# Travel Time Computation and Nested Logsum for AUCS 2.0

## Why

The AUCS 2.0 model uses a sophisticated accessibility framework based on random utility theory. For each origin hex `i` and destination `a`, we must:

1. Compute **generalized travel cost (GTC)** per mode (E1) incorporating in-vehicle time, wait, transfers, reliability, fares
2. Compute **mode utilities** with decay and nest parameters (E2)
3. Aggregate via **nested logsum** across mode nests (E3-E4) to get mode-choice-aware accessibility
4. Aggregate across time slices with weights to get final reach weight w_{i,a} (E5)

This is the mathematical core that converts travel times into accessibility values, enabling behavioral realism beyond simple distance buffers.

## What Changes

- Implement generalized travel cost (GTC) computation (E1) with all components:
  - In-vehicle time, wait time, access/egress walk, transfer penalties
  - Reliability buffers (by mode and time period)
  - Fare-to-time conversion using value-of-time (VOT)
  - Carry penalties for grocery/parcel categories
- Implement mode utility function (E2) with mode constants and comfort factors
- Implement nested logsum computation (E3-E4) with log-sum-exp numerical stability
- Implement time-slice aggregation (E5) for final accessibility weights
- Vectorize all computations using NumPy with Numba JIT compilation for performance
- Create accessibility matrix builders: hex-to-POI, hex-to-hub, hex-to-job-block
- Handle edge cases: unreachable destinations, mode unavailability, numerical overflow
- **BREAKING**: Establishes core accessibility computation used by ALL subscores

## Impact

- Affected specs: `generalized-cost`, `nested-logsum`, `travel-matrices` (all new)
- Affected code: Creates `src/Urban_Amenities2/` modules:
  - `math/gtc.py` - Generalized travel cost (E1)
  - `math/logsum.py` - Nested logsum (E2-E5) with stable numerics
  - `math/decay.py` - Distance/time decay kernels
  - `accessibility/matrices.py` - Accessibility matrix builders
  - `accessibility/weights.py` - w_{i,a} computation
- Dependencies: Adds numba, scipy
- Performance: Vectorized operations handle millions of OD pairs
- Outputs: `data/processed/accessibility_poi.parquet`, `accessibility_jobs.parquet`, etc.
