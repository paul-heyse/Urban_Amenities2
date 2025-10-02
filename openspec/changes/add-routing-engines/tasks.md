## 1. OSRM Integration

- [ ] 1.1 Create OSRM graph extracts from Overture Transportation for car, bike, foot profiles
- [ ] 1.2 Implement OSRM HTTP client in `src/Urban_Amenities2/router/osrm.py`
- [ ] 1.3 Add `/route` API calls with duration and distance extraction
- [ ] 1.4 Add `/table` API calls for many-to-many matrices with batching (max 100×100)
- [ ] 1.5 Handle snapping errors and fallback strategies
- [ ] 1.6 Write tests for OSRM client

## 2. OTP2 Integration

- [ ] 2.1 Build OTP2 graph from GTFS feeds + Overture streets
- [ ] 2.2 Implement OTP2 GraphQL (Transmodel) client in `src/Urban_Amenities2/router/otp.py`
- [ ] 2.3 Add trip plan queries with walk/transit/bike modes
- [ ] 2.4 Parse itineraries: walk_time, transit_time, wait_time, transfers, fare
- [ ] 2.5 Handle time window queries (AM peak, midday, PM peak, etc.)
- [ ] 2.6 Write tests for OTP2 client

## 3. Unified Routing API

- [ ] 3.1 Create unified interface in `src/Urban_Amenities2/router/api.py`
- [ ] 3.2 Normalize outputs to common schema (origin_hex, dest_hex, mode, period, duration_min)
- [ ] 3.3 Route mode selection (OSRM vs OTP) based on mode parameter
- [ ] 3.4 Write tests for unified API

## 4. Travel Time Matrix Computation

- [ ] 4.1 Implement batched matrix builder in `src/Urban_Amenities2/router/batch.py`
- [ ] 4.2 Compute hex-to-POI matrices by mode and period
- [ ] 4.3 Add caching layer with diskcache (keyed by origin/dest tiles, mode, period, data version)
- [ ] 4.4 Handle large OD pairs with spatial clustering and parallel requests
- [ ] 4.5 Write output Parquet files: `skims_{mode}_{period}.parquet`
- [ ] 4.6 Write tests

## 5. CLI and Documentation

- [ ] 5.1 Add `aucs routing build-osrm --profile car` command
- [ ] 5.2 Add `aucs routing build-otp --gtfs-dir data/processed/gtfs` command
- [ ] 5.3 Add `aucs routing compute-skims --hexes data/processed/hex_index.parquet` command
- [ ] 5.4 Write `docs/routing.md` explaining setup and usage
