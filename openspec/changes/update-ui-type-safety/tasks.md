## 1. UI typing plan
- [ ] 1.1 Confirm stub support and add any UI-specific typing utilities (Plotly trace aliases, Dash component protocols) if required.
- [ ] 1.2 Refactor `ui/performance.py` to avoid `None` values in typed dictionaries and ensure return types are concrete.
- [ ] 1.3 Harden selection helpers (`ui/hex_selection.py`, `ui/export.py`) so stored state uses typed objects and conversions, updating tests as needed.
- [ ] 1.4 Annotate Dash layers & callbacks (`ui/layers.py`, `ui/callbacks.py`, `ui/layouts/*`) with explicit input/output types and fix option payload construction.
- [ ] 1.5 Update `ui/logging.py` and shared helpers to return correctly typed loggers.
- [ ] 1.6 Run `mypy src/Urban_Amenities2/ui --warn-unused-ignores` and update docs with UI typing guidance.
