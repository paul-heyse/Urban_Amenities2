## 1. Ingestion typing clean-up
- [ ] 1.1 Define typed fallbacks for optional dependencies (BigQuery client, shapely) and ensure module-level imports do not assign `None` to typed modules.
- [ ] 1.2 Annotate Overture readers to return typed DataFrames/GeoDataFrames and accept typed parameters (`Mapping`, `Path`).
- [ ] 1.3 Update RIDB and Wikipedia clients to use typed request parameter structures; add tests for request serialization.
- [ ] 1.4 Ensure GTFS realtime fallback serializer/deserializer returns concrete types (`bytes`, dataclasses) and integrate with existing tests.
- [ ] 1.5 Execute `mypy src/Urban_Amenities2/io --warn-unused-ignores` and update ingestion documentation with new typing guidelines.
