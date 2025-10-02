## 1. Generalized Travel Cost (E1)

- [x] 1.1 Implement GTC function in `src/Urban_Amenities2/math/gtc.py`
- [x] 1.2 Add in-vehicle time component with θ_iv
- [x] 1.3 Add wait time component with θ_wait (transit only)
- [x] 1.4 Add access/egress walk component with θ_walk
- [x] 1.5 Add transfer penalty δ_m × num_transfers
- [x] 1.6 Add reliability buffer ρ_{m,τ} × travel_time_variance
- [x] 1.7 Add fare-to-time conversion: fare / VOT_τ
- [x] 1.8 Add carry penalty for grocery/parcel categories
- [x] 1.9 Vectorize across all OD pairs × modes
- [x] 1.10 Write comprehensive tests

## 2. Mode Utility and Nested Logsum (E2-E5)

- [x] 2.1 Implement mode utility in `src/Urban_Amenities2/math/logsum.py`
- [x] 2.2 Compute U_{i,a,m,τ} = β_m0 - α_m · GTC + γ_m · Comfort
- [x] 2.3 Implement nest-level inclusive value (E3) with log-sum-exp stability
- [x] 2.4 Implement top-level logsum (E4) across nests
- [x] 2.5 Add time-slice weighted aggregation (E5) → w_{i,a}
- [x] 2.6 Use Numba JIT for performance
- [x] 2.7 Write tests verifying numerical stability and properties

## 3. Accessibility Matrices

- [x] 3.1 Create matrix builders in `src/Urban_Amenities2/accessibility/matrices.py`
- [x] 3.2 Build hex-to-POI accessibility matrix with w_{i,a}
- [x] 3.3 Build hex-to-job-block matrix
- [x] 3.4 Build hex-to-hub/airport matrix
- [x] 3.5 Handle unreachable destinations (set w=0)
- [x] 3.6 Write output Parquet files
- [x] 3.7 Write tests

## 4. Integration and Performance

- [x] 4.1 Integrate with routing skims from add-routing-engines
- [x] 4.2 Optimize memory usage for large matrices (chunk processing)
- [x] 4.3 Add progress logging and ETA
- [x] 4.4 Profile performance and optimize bottlenecks
- [x] 4.5 Write integration tests
