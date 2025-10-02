"""Home page summarising key metrics."""

from __future__ import annotations

from dash import dash_table, html, register_page

from . import DATA_CONTEXT

register_page(__name__, path="/", name="Overview")


def layout(**_) -> html.Div:
    context = DATA_CONTEXT
    summary = context.summarise() if context else None
    table = dash_table.DataTable(
        id="summary-table",
        data=summary.reset_index().rename(columns={"index": "metric"}).to_dict("records") if summary is not None else [],
        columns=[{"name": col.title(), "id": col} for col in (summary.reset_index().columns if summary is not None else ["metric", "min", "max", "mean"])],
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
