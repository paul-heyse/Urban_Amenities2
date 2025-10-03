from __future__ import annotations

import pandas as pd

from Urban_Amenities2.io.enrichment import wikidata


def test_build_query_contains_coordinates() -> None:
    query = wikidata.build_query("Central Park", 40.0, -73.9, radius_km=1.2)
    assert "Central Park" in query
    assert "-73.9" in query
    assert "1.2" in query


def test_wikidata_enricher_match_returns_fields() -> None:
    class StubClient:
        def query(self, _: str) -> dict[str, object]:
            return {
                "results": {
                    "bindings": [
                        {
                            "item": {"value": "https://www.wikidata.org/entity/Q123"},
                            "capacity": {"value": "1000"},
                            "heritage": {"value": "Q234"},
                        }
                    ]
                }
            }

    enricher = wikidata.WikidataEnricher(client=StubClient())
    result = enricher.match("Place", 40.0, -73.9)
    assert result == {"wikidata_qid": "Q123", "capacity": "1000", "heritage_status": "Q234"}


def test_wikidata_enricher_handles_missing_results() -> None:
    class EmptyClient:
        def query(self, _: str) -> dict[str, object]:
            return {"results": {"bindings": []}}

    enricher = wikidata.WikidataEnricher(client=EmptyClient())
    result = enricher.match("Unknown", 0.0, 0.0)
    assert result == {"wikidata_qid": None, "capacity": None, "heritage_status": None}


def test_wikidata_enricher_enriches_dataframe() -> None:
    class RecordingClient:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def query(self, _: str) -> dict[str, object]:
            self.calls.append("called")
            return {"results": {"bindings": []}}

    pois = pd.DataFrame(
        {"poi_id": ["a", "b"], "name": ["One", "Two"], "lat": [1.0, 2.0], "lon": [3.0, 4.0]}
    )
    client = RecordingClient()
    enricher = wikidata.WikidataEnricher(client=client)
    result = enricher.enrich(pois)
    assert len(result) == 2
    assert all(result["wikidata_qid"].isna())
    assert client.calls == ["called", "called"]
