## 1. Baseline & Planning
- [x] 1.1 Capture current mypy errors across `ui/components`, `ui/layers`, `ui/callbacks`, `ui/layouts`
- [x] 1.2 Map component props/returns and callback inputs/outputs needing types

## 2. Component Typing
- [x] 2.1 Define TypedDicts/Enums for filter options, overlay controls, scoreboard entries
- [x] 2.2 Annotate component factories (filters, overlay controls, choropleth) with typed props
- [x] 2.3 Refactor `ui/layers.py` to build typed Plotly figure structures

## 3. Callback Typing
- [x] 3.1 Add typed decorators/wrapper utilities for Dash callbacks
- [x] 3.2 Annotate callback functions (map updates, filter changes, data refresh/export) with typed params/returns
- [x] 3.3 Update `ui/layouts` to pass typed data context objects/props

## 4. Tests & Docs
- [x] 4.1 Expand UI tests to assert typed callback behaviour and component payloads
- [x] 4.2 Document patterns for typed Dash development in developer guides
- [x] 4.3 Ensure mypy passes on targeted modules with strict settings

## 5. Validation
- [x] 5.1 Run pytest UI suite; confirm no regressions
- [x] 5.2 Capture before/after mypy reports for change log
- [x] 5.3 Submit for review and archive change upon approval
