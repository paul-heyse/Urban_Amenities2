# Routing Engines Integration for AUCS 2.0

## Why

AUCS 2.0 requires multi-modal travel time computation across walk, bike, car, and transit modes. This demands integration with:

- **OSRM** for car/bike/foot routing over Overture road networks
- **OTP2** for transit routing using GTFS + street networks

These routing engines provide the travel time matrices (T_{i→p,m}) that feed into the generalized travel cost equations (E1) and enable all accessibility scoring.

Without routing engines, we cannot compute mode-specific reachability, which is the foundation of the AUCS model's behavioral realism.

## What Changes

- Build OSRM extracts from Overture Transportation segments for car, bike, and foot profiles
- Create OSRM HTTP client for `/route` and `/table` APIs with batching and caching
- Build OTP2 graph from Overture streets + GTFS feeds for all CO/UT/ID agencies
- Create OTP2 GraphQL (Transmodel) client for transit trip planning and isochrones
- Implement unified routing API that abstracts OSRM vs OTP differences
- Create travel time matrix computation with batching and hex-to-hex caching
- Handle routing errors, snapping issues, and fallback strategies
- **BREAKING**: Requires OSRM and OTP2 external services (Docker containers or remote instances)

## Impact

- Affected specs: `osrm-integration`, `otp-integration`, `routing-api` (all new)
- Affected code: Creates `src/Urban_Amenities2/` modules:
  - `router/osrm.py` - OSRM client and profile management
  - `router/otp.py` - OTP2 GraphQL client
  - `router/api.py` - Unified routing interface
  - `router/batch.py` - Batch matrix computation
  - `router/cache.py` - Travel time caching
- Dependencies: Adds httpx, gql[requests], diskcache
- External services: Requires OSRM (3 profiles) and OTP2 (1 graph per market) running
- Outputs travel time skims: `data/processed/skims_{mode}_{period}.parquet`
