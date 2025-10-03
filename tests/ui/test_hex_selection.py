from __future__ import annotations

import pandas as pd
import pytest

from Urban_Amenities2.ui.hex_selection import HexDetails, HexSelector


def test_hex_details_from_row(sample_scores: pd.DataFrame) -> None:
    row = sample_scores.iloc[0]
    details = HexDetails.from_row(row)

    assert details.hex_id == row["hex_id"]
    assert details.state == "CO"
    assert details.aucs == pytest.approx(75.0)
    assert details.top_amenities[0]["name"] == "Library"
    assert details.top_modes["transit"] == pytest.approx(0.4)


def test_hex_selector_selection_flow(sample_scores: pd.DataFrame) -> None:
    selector = HexSelector(sample_scores)
    selector.max_selection = 2

    assert selector.select_hex("abc123") is True
    assert selector.select_hex("abc123") is True  # duplicate allowed, no change
    assert selector.select_hex("def456") is True
    assert selector.select_hex("ghi789") is False  # limit reached
    assert selector.selected_hexes == ["abc123", "def456"]

    selector.deselect_hex("abc123")
    assert selector.selected_hexes == ["def456"]

    selector.clear_selection()
    assert selector.selected_hexes == []


def test_hex_selector_get_details_and_neighbors(
    sample_scores: pd.DataFrame, fake_h3
) -> None:
    selector = HexSelector(sample_scores)
    selector.select_hex("abc123")

    details = selector.get_details("abc123")
    assert isinstance(details, HexDetails)
    assert details.metro == "Denver"

    assert selector.get_details("missing") is None

    neighbors = selector.get_neighbors("abc123", k=2)
    # Fake H3 returns the id plus two derived neighbours; only ids in the dataframe remain.
    assert neighbors.equals(sample_scores[sample_scores["hex_id"] == "abc123"]) is True


def test_hex_selector_comparison_data(sample_scores: pd.DataFrame) -> None:
    selector = HexSelector(sample_scores)
    selector.select_hex("abc123")
    selector.select_hex("def456")

    comparison = selector.get_comparison_data()
    assert list(comparison["hex_id"]) == ["abc123", "def456"]

    selector.clear_selection()
    empty = selector.get_comparison_data()
    assert empty.empty
