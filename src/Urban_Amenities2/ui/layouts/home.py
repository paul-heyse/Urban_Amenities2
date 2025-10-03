"""Home page summarising key metrics."""

from __future__ import annotations

from importlib import import_module
from typing import Any, Callable, cast

from dash import html, register_page as _register_page

dash_table = cast(Any, import_module("dash_table"))

from . import DATA_CONTEXT

register_page = cast(Callable[..., None], _register_page)
register_page(__name__, path="/", name="Overview")


def layout(**_: object) -> html.Div:
    context = DATA_CONTEXT
    summary = context.summarise() if context else None
    if summary is not None and not summary.empty:
        reset = summary.reset_index().rename(columns={"index": "metric"})
        data = reset.to_dict("records")
        columns = [{"name": col.title(), "id": col} for col in reset.columns]
    else:
        data = []
        columns = [{"name": col.title(), "id": col} for col in ("metric", "min", "max", "mean")]
    table = dash_table.DataTable(
        id="summary-table",
        data=data,
        columns=columns,
        sort_action="native",
        page_size=10,
    )
    return html.Div(
        className="page overview-page",
        children=[
            html.H2("Urban Amenities Overview"),
            html.P("Explore composite scores, category distribution, and recent model runs."),
            table,
        ],
    )


__all__ = ["layout"]
