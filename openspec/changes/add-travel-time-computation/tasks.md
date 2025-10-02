## 1. Generalized Travel Cost (E1)

- [ ] 1.1 Implement GTC function in `src/Urban_Amenities2/math/gtc.py`
- [ ] 1.2 Add in-vehicle time component with θ_iv
- [ ] 1.3 Add wait time component with θ_wait (transit only)
- [ ] 1.4 Add access/egress walk component with θ_walk
- [ ] 1.5 Add transfer penalty δ_m × num_transfers
- [ ] 1.6 Add reliability buffer ρ_{m,τ} × travel_time_variance
- [ ] 1.7 Add fare-to-time conversion: fare / VOT_τ
- [ ] 1.8 Add carry penalty for grocery/parcel categories
- [ ] 1.9 Vectorize across all OD pairs × modes
- [ ] 1.10 Write comprehensive tests

## 2. Mode Utility and Nested Logsum (E2-E5)

- [ ] 2.1 Implement mode utility in `src/Urban_Amenities2/math/logsum.py`
- [ ] 2.2 Compute U_{i,a,m,τ} = β_m0 - α_m · GTC + γ_m · Comfort
- [ ] 2.3 Implement nest-level inclusive value (E3) with log-sum-exp stability
- [ ] 2.4 Implement top-level logsum (E4) across nests
- [ ] 2.5 Add time-slice weighted aggregation (E5) → w_{i,a}
- [ ] 2.6 Use Numba JIT for performance
- [ ] 2.7 Write tests verifying numerical stability and properties

## 3. Accessibility Matrices

- [ ] 3.1 Create matrix builders in `src/Urban_Amenities2/accessibility/matrices.py`
- [ ] 3.2 Build hex-to-POI accessibility matrix with w_{i,a}
- [ ] 3.3 Build hex-to-job-block matrix
- [ ] 3.4 Build hex-to-hub/airport matrix
- [ ] 3.5 Handle unreachable destinations (set w=0)
- [ ] 3.6 Write output Parquet files
- [ ] 3.7 Write tests

## 4. Integration and Performance

- [ ] 4.1 Integrate with routing skims from add-routing-engines
- [ ] 4.2 Optimize memory usage for large matrices (chunk processing)
- [ ] 4.3 Add progress logging and ETA
- [ ] 4.4 Profile performance and optimize bottlenecks
- [ ] 4.5 Write integration tests
