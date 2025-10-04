# Contributing Guidelines

## Testing & Coverage Expectations

- Run `pytest -q --cov=src --cov-branch` locally before submitting changes.
- The project targets **≥95% line coverage** and **≥90% branch coverage** across first-party modules.
- New features must include unit tests; regressions require reproducer tests to guard against future breaks.
- When coverage dips below the thresholds, expand tests or mark legitimately unreachable lines with `# pragma: no cover` and a brief comment.
- Upload HTML reports via `coverage html` when investigating gaps; artifacts should be attached to CI jobs for reviewer insight.

## Reusable Test Fixtures

The shared fixtures in `tests/conftest.py` provide:

- `cache_manager`: isolated `CacheManager` instance with automatic cleanup.
- `data_context` & `ui_settings`: disk-backed Dash dataset seeded with synthetic overlays for UI tests.
- `osrm_stub_session` / `otp_stub_session`: deterministic HTTP stubs for routing clients.

Prefer these fixtures over ad-hoc mocks to keep scenarios consistent and fast.

## UI Typing Expectations

- Run `python -m mypy src/Urban_Amenities2/ui --warn-unused-ignores` before submitting UI changes; keep the UI package clean of `Any` leaks.
- Reuse helper types or factories (e.g., `DropdownOption`, `MapboxLayer`, test factories in `tests/ui_factories.py`) instead of ad-hoc dicts.
- When adding new UI tests, prefer the shared factories so datasets stay aligned with typed interfaces.

## Type Safety Patterns

- Prefer runtime validation helpers over blanket `typing.cast`.  The utilities in
  `Urban_Amenities2.utils.types` provide guardrails such as
  `cast_to_dataframe` (fail if a Series slips through) and `ensure_dataframe`
  (promote Series to a single-column DataFrame).  Use them whenever a pandas API
  returns ``DataFrame | Series``.
- Validate optional values before arithmetic.  For routing responses, check for
  ``None`` explicitly (`if value is None: return`) before comparing or
  normalising values; log a warning for unexpected gaps.
- When mapping dynamic dictionaries to stricter types, confirm key/value types
  at runtime (``all(isinstance(key, str) for key in mapping)``) before treating
  them as strongly typed structures.
- Document any remaining ``# type: ignore[code]`` usages inline with the error
  code and a short justification so `warn_unused_ignores = True` remains useful.

## Pull Request Checklist

1. Format and lint (`black`, `ruff`) before opening a PR.
2. Ensure coverage thresholds are met; failing coverage gates will block merges.
3. Update documentation or changelogs when behaviour changes.
4. Reference relevant OpenSpec tasks in commit messages when applicable.
