## 1. Baseline & Planning
- [ ] 1.1 Capture current mypy errors across `ui/components`, `ui/layers`, `ui/callbacks`, `ui/layouts`
- [ ] 1.2 Map component props/returns and callback inputs/outputs needing types

## 2. Component Typing
- [ ] 2.1 Define TypedDicts/Enums for filter options, overlay controls, scoreboard entries
- [ ] 2.2 Annotate component factories (filters, overlay controls, choropleth) with typed props
- [ ] 2.3 Refactor `ui/layers.py` to build typed Plotly figure structures

## 3. Callback Typing
- [ ] 3.1 Add typed decorators/wrapper utilities for Dash callbacks
- [ ] 3.2 Annotate callback functions (map updates, filter changes, data refresh/export) with typed params/returns
- [ ] 3.3 Update `ui/layouts` to pass typed data context objects/props

## 4. Tests & Docs
- [ ] 4.1 Expand UI tests to assert typed callback behaviour and component payloads
- [ ] 4.2 Document patterns for typed Dash development in developer guides
- [ ] 4.3 Ensure mypy passes on targeted modules with strict settings

## 5. Validation
- [ ] 5.1 Run pytest UI suite; confirm no regressions
- [ ] 5.2 Capture before/after mypy reports for change log
- [ ] 5.3 Submit for review and archive change upon approval
