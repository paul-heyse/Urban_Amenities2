from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

import pandas as pd

from ...hex.aggregation import points_to_hex
from ...logging_utils import get_logger
from ...versioning.snapshots import SnapshotRegistry
from .registry import Agency

LOGGER = get_logger("aucs.ingest.gtfs.static")


@dataclass
class GTFSCache:
    directory: Path = Path("data/cache/gtfs")

    def path_for(self, agency: Agency) -> Path:
        sanitized = agency.name.lower().replace(" ", "_").replace("/", "-")
        return self.directory / f"{sanitized}.zip"


class GTFSStaticIngestor:
    def __init__(self, cache: GTFSCache | None = None, registry: SnapshotRegistry | None = None):
        self.cache = cache or GTFSCache()
        self.registry = registry or SnapshotRegistry(Path("data/snapshots.jsonl"))
        self.cache.directory.mkdir(parents=True, exist_ok=True)

    def download(self, agency: Agency, session=None) -> Path:
        if agency.static_url is None:
            raise ValueError(f"Agency {agency.name} does not define a static GTFS URL")
        import fsspec

        target = self.cache.path_for(agency)
        with fsspec.open(agency.static_url, mode="rb") as handle:
            data = handle.read()
        if not self.registry.has_changed(agency.name, data) and target.exists():
            LOGGER.info("gtfs_static_unchanged", agency=agency.name)
            return target
        target.write_bytes(data)
        self.registry.record_snapshot(agency.name, agency.static_url, data)
        LOGGER.info("cached_gtfs_static", agency=agency.name, path=str(target))
        return target

    def parse(self, path: Path) -> dict[str, pd.DataFrame]:
        with zipfile.ZipFile(path) as archive:
            datasets: dict[str, pd.DataFrame] = {}
            for name in ("stops.txt", "routes.txt", "trips.txt", "stop_times.txt", "calendar.txt"):
                if name not in archive.namelist():
                    continue
                with archive.open(name) as file_obj:
                    datasets[name[:-4]] = pd.read_csv(io.TextIOWrapper(file_obj, encoding="utf-8"))
        return datasets

    def compute_headways(self, stop_times: pd.DataFrame, trips: pd.DataFrame) -> pd.DataFrame:
        merged = stop_times.merge(trips[["trip_id", "route_id"]], on="trip_id", how="left")
        merged = merged[merged["arrival_time"].notna()].copy()
        merged["seconds"] = merged["arrival_time"].apply(_time_to_seconds)
        grouped = merged.groupby("route_id")
        records = []
        for route_id, group in grouped:
            times = sorted(group["seconds"].tolist())
            if len(times) < 2:
                continue
            deltas = [t2 - t1 for t1, t2 in zip(times, times[1:], strict=False) if t2 > t1]
            if not deltas:
                continue
            mean_headway = sum(deltas) / len(deltas) / 60.0
            span = (min(times), max(times))
            records.append(
                {
                    "route_id": route_id,
                    "mean_headway_min": mean_headway,
                    "service_span_min": span[0] / 60.0,
                    "service_end_min": span[1] / 60.0,
                }
            )
        return pd.DataFrame.from_records(records)

    def index_stops(self, stops: pd.DataFrame) -> pd.DataFrame:
        if stops.empty:
            return stops.assign(hex_id=[])
        stops = points_to_hex(stops, lat_column="stop_lat", lon_column="stop_lon", hex_column="hex_id")
        return stops

    def write_outputs(
        self,
        agency: Agency,
        datasets: dict[str, pd.DataFrame],
        output_dir: Path = Path("data/processed"),
    ) -> dict[str, Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        paths: dict[str, Path] = {}
        if "stops" in datasets:
            stops = self.index_stops(datasets["stops"])
            path = output_dir / "gtfs_stops.parquet"
            stops.to_parquet(path)
            paths["stops"] = path
        if "routes" in datasets:
            path = output_dir / "gtfs_routes.parquet"
            datasets["routes"].to_parquet(path)
            paths["routes"] = path
        if "stop_times" in datasets and "trips" in datasets:
            headways = self.compute_headways(datasets["stop_times"], datasets["trips"])
            path = output_dir / "gtfs_headways.parquet"
            headways.to_parquet(path)
            paths["headways"] = path
        return paths

    def ingest(self, agency: Agency, session=None, output_dir: Path = Path("data/processed")) -> dict[str, Path]:
        path = self.download(agency, session=session)
        datasets = self.parse(path)
        return self.write_outputs(agency, datasets, output_dir=output_dir)


def _time_to_seconds(value: str) -> int:
    parts = value.split(":")
    if len(parts) != 3:
        raise ValueError(f"Invalid GTFS time format: {value}")
    hours, minutes, seconds = (int(part) for part in parts)
    return int(timedelta(hours=hours, minutes=minutes, seconds=seconds).total_seconds())


__all__ = ["GTFSStaticIngestor", "GTFSCache"]
