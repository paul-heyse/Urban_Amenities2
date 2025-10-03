## 1. Routing & monitoring typing
- [ ] 1.1 Formalize OSRM request/response schemas (typed params, parsed tables) and refactor `_concatenate_rows` helpers.
- [ ] 1.2 Replace union-heavy accumulators in `monitoring/metrics.py` with typed data classes or protocol-backed collectors; ensure `metrics.record()` returns `None`.
- [ ] 1.3 Annotate `monitoring/health.py` optional psutil import using typed fallbacks consistent with new typing strategy.
- [ ] 1.4 Update CLI export sanitisation to operate on `dict[str, object]` payloads and adjust tests to cover typed result.
- [ ] 1.5 Run targeted typing checks (`mypy src/Urban_Amenities2/router src/Urban_Amenities2/monitoring src/Urban_Amenities2/cli --warn-unused-ignores`) and document routing typing conventions.
