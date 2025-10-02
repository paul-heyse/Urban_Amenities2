"""Example ingestion pipeline for Colorado data."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from Urban_Amenities2.io.gtfs.registry import load_registry
from Urban_Amenities2.io.gtfs.static import GTFSCache, GTFSStaticIngestor
from Urban_Amenities2.io.overture.places import ingest_places
from Urban_Amenities2.io.overture.transportation import export_networks, prepare_transportation
from Urban_Amenities2.io.quality.checks import generate_report
from Urban_Amenities2.io.versioning.snapshots import SnapshotRegistry

DATA_ROOT = Path("data")
PROCESSED = DATA_ROOT / "processed"
RAW = DATA_ROOT / "raw"


def ingest_overture_places() -> None:
    parquet_path = RAW / "overture_places_co.parquet"
    if not parquet_path.exists():
        print(f"Skipping Overture Places – expected {parquet_path}")
        return
    ingest_places(parquet_path, output_path=PROCESSED / "pois.parquet")
    print("Wrote POIs to", PROCESSED / "pois.parquet")


def ingest_gtfs() -> None:
    registry = load_registry()
    cache = GTFSCache(directory=DATA_ROOT / "cache" / "gtfs")
    snapshot_path = DATA_ROOT / "snapshots" / "gtfs.jsonl"
    static = GTFSStaticIngestor(cache=cache, registry=SnapshotRegistry(snapshot_path))
    output_dir = PROCESSED
    for agency in registry:
        if agency.state != "CO":
            continue
        print(f"Ingesting {agency.name}")
        static.ingest(agency, output_dir=output_dir)


def prepare_transport_network() -> None:
    segments_path = RAW / "transport_segments_co.parquet"
    if not segments_path.exists():
        print(f"Skipping transportation export – expected {segments_path}")
        return
    frame = pd.read_parquet(segments_path)
    prepared = prepare_transportation(frame)
    export_networks(prepared, output_root=PROCESSED)
    print("Exported OSRM GeoJSON files")


def build_quality_report() -> None:
    pois_path = PROCESSED / "pois.parquet"
    if not pois_path.exists():
        print("Quality report skipped – run POI ingestion first")
        return
    pois = pd.read_parquet(pois_path)
    report_dir = DATA_ROOT / "quality_reports"
    summary = generate_report(pois, output_dir=report_dir)
    print("Quality report written to", report_dir)
    print("Summary:", summary)


def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    ingest_overture_places()
    ingest_gtfs()
    prepare_transport_network()
    build_quality_report()


if __name__ == "__main__":
    main()
