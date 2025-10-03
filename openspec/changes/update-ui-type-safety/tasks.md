## 1. Inventory & Baseline
- [ ] 1.1 Catalogue dynamic constructs in `ui/` (callbacks, layout factories, data loader outputs)
- [ ] 1.2 Enumerate existing tests covering UI logic; note gaps
- [ ] 1.3 Record current mypy errors specific to UI modules

## 2. Typing the Data Layer
- [ ] 2.1 Define TypedDicts/dataclasses for overlay payloads, filter options, choropleth configurations
- [ ] 2.2 Annotate `ui/data_loader.py` return types and internal helpers; ensure compatibility with caching layer
- [ ] 2.3 Add typed factories for synthetic UI datasets used in tests

## 3. Typing Components & Callbacks
- [ ] 3.1 Annotate Dash components (filters, overlay controls, hex selection) with typed props/returns
- [ ] 3.2 Type Dash callback signatures, ensuring inputs/outputs align with typed helper structures
- [ ] 3.3 Update `ui/callbacks.py` logic to avoid implicit Any operations (e.g., typed conversions, guard clauses)

## 4. Layouts & Export Logic
- [ ] 4.1 Annotate layout factory functions (`layouts/*.py`) and ensure typed params/context usage
- [ ] 4.2 Type `ui/export.py` pathway (CSV/GeoJSON) including geometry conversions
- [ ] 4.3 Ensure caches and session state interactions have explicit typed interfaces

## 5. Tests & Tooling
- [ ] 5.1 Update UI unit tests to construct typed payloads, mocking typed repositories where needed
- [ ] 5.2 Run mypy targeting `src/Urban_Amenities2/ui` with strict settings; resolve all errors
- [ ] 5.3 Integrate UI typing guidance into developer docs / CONTRIBUTING.md
- [ ] 5.4 Update CI workflow to include UI mypy target as a required check

## 6. Validation
- [ ] 6.1 Execute pytest UI suite; ensure no regressions
- [ ] 6.2 Capture before/after mypy reports for UI modules and attach to change record
- [ ] 6.3 Request review, merge, and archive change after approval
