## 1. OSRM Integration

- [x] 1.1 Create OSRM graph extracts from Overture Transportation for car, bike, foot profiles
- [x] 1.2 Implement OSRM HTTP client in `src/Urban_Amenities2/router/osrm.py`
- [x] 1.3 Add `/route` API calls with duration and distance extraction
- [x] 1.4 Add `/table` API calls for many-to-many matrices with batching (max 100×100)
- [x] 1.5 Handle snapping errors and fallback strategies
- [x] 1.6 Write tests for OSRM client

## 2. OTP2 Integration

- [x] 2.1 Build OTP2 graph from GTFS feeds + Overture streets
- [x] 2.2 Implement OTP2 GraphQL (Transmodel) client in `src/Urban_Amenities2/router/otp.py`
- [x] 2.3 Add trip plan queries with walk/transit/bike modes
- [x] 2.4 Parse itineraries: walk_time, transit_time, wait_time, transfers, fare
- [x] 2.5 Handle time window queries (AM peak, midday, PM peak, etc.)
- [x] 2.6 Write tests for OTP2 client

## 3. Unified Routing API

- [x] 3.1 Create unified interface in `src/Urban_Amenities2/router/api.py`
- [x] 3.2 Normalize outputs to common schema (origin_hex, dest_hex, mode, period, duration_min)
- [x] 3.3 Route mode selection (OSRM vs OTP) based on mode parameter
- [x] 3.4 Write tests for unified API

## 4. Travel Time Matrix Computation

- [x] 4.1 Implement batched matrix builder in `src/Urban_Amenities2/router/batch.py`
- [x] 4.2 Compute hex-to-POI matrices by mode and period
- [x] 4.3 Add caching layer with diskcache (keyed by origin/dest tiles, mode, period, data version)
- [x] 4.4 Handle large OD pairs with spatial clustering and parallel requests
- [x] 4.5 Write output Parquet files: `skims_{mode}_{period}.parquet`
- [x] 4.6 Write tests

## 5. CLI and Documentation

- [x] 5.1 Add `aucs routing build-osrm --profile car` command
- [x] 5.2 Add `aucs routing build-otp --gtfs-dir data/processed/gtfs` command
- [x] 5.3 Add `aucs routing compute-skims --hexes data/processed/hex_index.parquet` command
- [x] 5.4 Write `docs/routing.md` explaining setup and usage
