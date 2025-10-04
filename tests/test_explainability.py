from __future__ import annotations

import pandas as pd

from Urban_Amenities2.scores.explainability import top_contributors


def test_top_contributors_extracts_sorted_records() -> None:
    frame = pd.DataFrame(
        [
            {
                "hex_id": "hex-1",
                "contributors": {
                    "food": [
                        {
                            "poi_id": "a",
                            "name": "Cafe",
                            "contribution": 0.2,
                            "quality": 0.9,
                            "quality_components": {"fresh": 0.8},
                            "brand_penalty": 0.1,
                        },
                        {
                            "poi_id": "b",
                            "name": "Bakery",
                            "contribution": 0.6,
                        },
                        {"poi_id": "c", "contribution": "not-a-number"},
                    ],
                    "ignored": "not-a-sequence",
                },
            },
            {"hex_id": "hex-2", "contributors": None},
        ]
    )

    result = top_contributors(frame, top_n=2)

    assert list(result["poi_id"]) == ["b", "a"]
    assert list(result["category"].unique()) == ["food"]
    assert result.loc[result["poi_id"] == "a", "brand_penalty"].iloc[0] == 0.1


def test_top_contributors_ignores_non_mapping_entries() -> None:
    frame = pd.DataFrame(
        [
            {"hex_id": "hex-3", "contributors": [1, None, "invalid"]},
            {"hex_id": "hex-4", "contributors": {"amenity": 1}},
        ]
    )

    result = top_contributors(frame)

    assert result.empty
