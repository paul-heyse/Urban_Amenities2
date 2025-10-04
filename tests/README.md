# Testing Guidelines

## I/O module conventions

- Prefer lightweight stub sessions or clients that capture request metadata (`method`,
  `params`, `headers`) and return deterministic payloads. This avoids relying on external
  network calls while still exercising pagination, retry, and caching logic.
- Store sample responses under `tests/fixtures/io_samples/` and load them via helper
  fixtures when the payload exceeds a few inline records.
- Patch coordinate utilities (`points_to_hex`, `lines_to_hex`, `latlon_to_hex`) in tests to
  avoid importing heavy geospatial stacks. The patches should assert on the inputs to
  confirm the ingest pipeline filters/cleans records before conversion.
- Use `pytest.MonkeyPatch` for temporary overrides and rely on `tests/io/conftest.py`
  fixtures for rate limiter and circuit breaker stubs when testing resilience.
- When validating parquet/geojson exports, redirect the write to a temporary directory and
  assert both the file creation and the shape of the returned dataframe.

## Shared fixtures

- `dummy_rate_limiter` / `dummy_breaker` – minimal implementations that track call counts
  without sleeping or raising, ideal for retry/backoff assertions.
- `StubSession` helpers (defined inline per test module) – queue HTTP responses and record
  each request so tests can validate pagination, auth headers, and cache snapshots.

## Coverage expectations

Run targeted suites during development:

```bash
pytest tests/io/ -q
```

Use the coverage command from the change tasks before opening a PR:

```bash
pytest tests/io/ -v --cov=src/Urban_Amenities2/io --cov-report=term-missing
```
