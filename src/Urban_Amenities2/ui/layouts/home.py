"""Home page summarising key metrics."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, cast

import pandas as pd  # type: ignore[import-untyped]
from dash import dash_table, html

from ..contracts import ScoreboardEntry
from ..dash_wrappers import register_page
from . import DATA_CONTEXT

register_page(__name__, path="/", name="Overview")


def _scoreboard_entries(summary: pd.DataFrame | None) -> list[ScoreboardEntry]:
    if summary is None or summary.empty or "aucs" not in summary.index:
        return []
    row = summary.loc["aucs"]
    entries: list[ScoreboardEntry] = []
    mean_value = float(row.get("mean", 0.0))
    entries.append(
        {
            "label": "Average AUCS",
            "value": mean_value,
            "unit": "pts",
            "description": "Mean composite score across all hexes",
        }
    )
    entries.append(
        {
            "label": "Best hex",
            "value": float(row.get("max", mean_value)),
            "unit": "pts",
            "description": "Highest AUCS value observed",
        }
    )
    entries.append(
        {
            "label": "Lowest hex",
            "value": float(row.get("min", mean_value)),
            "unit": "pts",
            "description": "Lowest AUCS value observed",
        }
    )
    return entries


def _render_scoreboard(entries: Sequence[ScoreboardEntry]) -> html.Div:
    cards = []
    for entry in entries:
        unit = entry.get("unit")
        value_text = f"{entry['value']:.1f}{f' {unit}' if unit else ''}"
        cards.append(
            html.Div(
                className="scoreboard-card",
                children=[
                    html.Span(entry["label"], className="scoreboard-label"),
                    html.Span(value_text, className="scoreboard-value"),
                    html.Span(entry.get("description", ""), className="scoreboard-description"),
                ],
            )
        )
    return html.Div(className="scoreboard", children=cards)


def layout(**_: Any) -> html.Div:
    context = DATA_CONTEXT
    summary = context.summarise() if context else None
    table_data: list[dict[str, Any]]
    table_columns: list[dict[str, str]]
    if summary is not None and not summary.empty:
        reset = summary.reset_index().rename(columns={"index": "metric"})
        table_data = reset.to_dict("records")
        table_columns = [{"name": column.title(), "id": column} for column in reset.columns]
    else:
        table_data = []
        table_columns = [
            {"name": "Metric", "id": "metric"},
            {"name": "Min", "id": "min"},
            {"name": "Max", "id": "max"},
            {"name": "Mean", "id": "mean"},
        ]
    data_table_factory = cast(Any, dash_table.DataTable)  # type: ignore[attr-defined]
    table = data_table_factory(
        id="summary-table",
        data=table_data,
        columns=table_columns,
        sort_action="native",
        page_size=10,
    )
    scoreboard = _render_scoreboard(_scoreboard_entries(summary))
    return html.Div(
        className="page overview-page",
        children=[
            html.H2("Urban Amenities Overview"),
            html.P("Explore composite scores, category distribution, and recent model runs."),
            scoreboard,
            table,
        ],
    )


__all__ = ["layout"]
