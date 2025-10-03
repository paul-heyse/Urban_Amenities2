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

## Pull Request Checklist

1. Format and lint (`black`, `ruff`) before opening a PR.
2. Ensure coverage thresholds are met; failing coverage gates will block merges.
3. Update documentation or changelogs when behaviour changes.
4. Reference relevant OpenSpec tasks in commit messages when applicable.
