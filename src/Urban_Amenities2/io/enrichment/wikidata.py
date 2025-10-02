from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import pandas as pd
from SPARQLWrapper import JSON, SPARQLWrapper


@dataclass
class WikidataClient:
    endpoint: str = "https://query.wikidata.org/sparql"
    user_agent: str = "UrbanAmenitiesBot/0.1"

    def __post_init__(self) -> None:
        self._client = SPARQLWrapper(self.endpoint, agent=self.user_agent)
        self._client.setReturnFormat(JSON)

    def query(self, query: str) -> Dict:
        self._client.setQuery(query)
        return self._client.query().convert()


def build_query(name: str, lat: float, lon: float, radius_km: float = 0.5) -> str:
    return f"""
    SELECT ?item ?itemLabel ?capacity ?heritage WHERE {{
      ?item rdfs:label "{name}"@en.
      SERVICE wikibase:around {{
        ?item wdt:P625 ?location .
        bd:serviceParam wikibase:center "Point({lon} {lat})"^^geo:wktLiteral .
        bd:serviceParam wikibase:radius "{radius_km}" .
      }}
      OPTIONAL {{ ?item wdt:P1083 ?capacity. }}
      OPTIONAL {{ ?item wdt:P1435 ?heritage. }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}
    LIMIT 1
    """


class WikidataEnricher:
    def __init__(self, client: WikidataClient | None = None):
        self.client = client or WikidataClient()

    def match(self, name: str, lat: float, lon: float) -> Dict[str, Optional[str]]:
        query = build_query(name, lat, lon)
        results = self.client.query(query)
        bindings = results.get("results", {}).get("bindings", [])
        if not bindings:
            return {"wikidata_qid": None, "capacity": None, "heritage_status": None}
        binding = bindings[0]
        qid = binding.get("item", {}).get("value", "")
        qid_short = qid.split("/")[-1] if qid else None
        capacity = binding.get("capacity", {}).get("value")
        heritage = binding.get("heritage", {}).get("value")
        return {"wikidata_qid": qid_short, "capacity": capacity, "heritage_status": heritage}

    def enrich(self, pois: pd.DataFrame) -> pd.DataFrame:
        records = []
        for _, row in pois.iterrows():
            result = self.match(row.get("name", ""), float(row.get("lat", 0.0)), float(row.get("lon", 0.0)))
            record = {"poi_id": row.get("poi_id"), **result}
            records.append(record)
        return pd.DataFrame.from_records(records)


__all__ = ["WikidataClient", "WikidataEnricher", "build_query"]
