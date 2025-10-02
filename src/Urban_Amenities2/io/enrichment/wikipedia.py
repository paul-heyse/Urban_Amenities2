from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional

import pandas as pd
import requests

API_URL = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{project}/all-access/all-agents/{title}/daily/{start}/{end}"


@dataclass
class WikipediaClient:
    project: str = "en.wikipedia.org"

    def fetch(self, title: str, months: int = 12, session: Optional[requests.Session] = None) -> pd.DataFrame:
        session = session or requests.Session()
        end = datetime.utcnow().date().replace(day=1) - timedelta(days=1)
        start = end - timedelta(days=30 * months)
        url = API_URL.format(
            project=self.project,
            title=title.replace(" ", "_"),
            start=start.strftime("%Y%m%d"),
            end=end.strftime("%Y%m%d"),
        )
        response = session.get(url, timeout=30)
        response.raise_for_status()
        data = response.json().get("items", [])
        frame = pd.DataFrame(data)
        if frame.empty:
            return pd.DataFrame(columns=["timestamp", "views"])
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], format="%Y%m%d00")
        frame = frame.rename(columns={"views": "pageviews"})
        return frame[["timestamp", "pageviews"]]


def compute_statistics(pageviews: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    records = []
    for title, frame in pageviews.items():
        if frame.empty:
            records.append({"title": title, "median_views": 0.0, "iqr": 0.0})
            continue
        median = float(frame["pageviews"].median())
        q1 = frame["pageviews"].quantile(0.25)
        q3 = frame["pageviews"].quantile(0.75)
        records.append({"title": title, "median_views": median, "iqr": float(q3 - q1)})
    summary = pd.DataFrame.from_records(records)
    if summary.empty:
        return summary
    mean = summary["median_views"].mean()
    std = summary["median_views"].std(ddof=0) or 1.0
    summary["popularity_z"] = (summary["median_views"] - mean) / std
    return summary


def enrich_with_pageviews(titles: Dict[str, str], client: WikipediaClient | None = None) -> pd.DataFrame:
    client = client or WikipediaClient()
    pageview_data: Dict[str, pd.DataFrame] = {}
    for poi_id, title in titles.items():
        frame = client.fetch(title)
        pageview_data[poi_id] = frame
    stats = compute_statistics({poi_id: frame for poi_id, frame in pageview_data.items()})
    stats = stats.rename(columns={"title": "poi_id"})
    stats["poi_id"] = stats["poi_id"].astype(str)
    stats["title"] = [titles.get(poi_id, "") for poi_id in stats["poi_id"]]
    return stats


__all__ = ["WikipediaClient", "enrich_with_pageviews", "compute_statistics"]
