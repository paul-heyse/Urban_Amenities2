"""Benchmark viewport and aggregation performance for the UI data layer."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Iterable, List, Sequence

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from Urban_Amenities2.ui.config import UISettings
from Urban_Amenities2.ui.data_loader import DataContext
from Urban_Amenities2.ui.layers import basemap_options
from Urban_Amenities2.ui.components.choropleth import create_choropleth


def _generate_hexes(count: int, resolution: int = 9) -> List[str]:
    h3 = __import__("h3")
    origin = h3.latlng_to_cell(39.5, -111.0, resolution)
    if count <= 1:
        return [origin]
    approximate_k = int(((-3 + (12 * count - 3) ** 0.5) / 6)) + 1
    cells = h3.grid_disk(origin, approximate_k)
    if len(cells) < count:
        cells = h3.grid_disk(origin, approximate_k + 1)
    return list(cells)[:count]


def _build_context(size: int, resolution: int = 9) -> DataContext:
    hexes = _generate_hexes(size, resolution=resolution)
    rng = np.random.default_rng(42)
    scores = pd.DataFrame(
        {
            "hex_id": hexes,
            "aucs": rng.uniform(0, 100, size),
            "EA": rng.uniform(0, 100, size),
            "state": rng.choice(["CO", "UT", "ID"], size=size),
            "metro": rng.choice(
                ["Denver", "Salt Lake City", "Boise", "Colorado Springs"], size=size
            ),
            "county": rng.choice(
                ["Denver County", "Salt Lake County", "Ada County", "Utah County"], size=size
            ),
        }
    )
    context = DataContext(settings=UISettings())
    context.scores = scores
    context.metadata = scores[["hex_id", "state", "metro", "county"]]
    context._prepare_geometries()
    context.validate_geometries()
    context._record_base_resolution()
    return context


def _viewport(bounds: Sequence[float]) -> tuple[float, float, float, float]:
    lon_min, lat_min, lon_max, lat_max = bounds
    lon_span = (lon_max - lon_min) * 0.25
    lat_span = (lat_max - lat_min) * 0.25
    lon_center = (lon_max + lon_min) / 2
    lat_center = (lat_max + lat_min) / 2
    return (
        lon_center - lon_span,
        lat_center - lat_span,
        lon_center + lon_span,
        lat_center + lat_span,
    )


def benchmark_sizes(sizes: Iterable[int]) -> None:
    for size in sizes:
        context = _build_context(size)
        bounds = context.bounds
        viewport = _viewport(bounds) if bounds else None
        print(f"\nDataset size: {size:,} hexes")
        print("resolution\tframe_size\tviewport_size\taggregation_ms\tviewport_ms")
        for resolution in (6, 7, 8, context.base_resolution or 9):
            start = time.perf_counter()
            frame = context.frame_for_resolution(resolution, columns=["aucs", "EA"])
            aggregation_ms = (time.perf_counter() - start) * 1000
            slice_start = time.perf_counter()
            trimmed = context.apply_viewport(frame, resolution, viewport)
            viewport_ms = (time.perf_counter() - slice_start) * 1000
            print(
                f"{resolution}\t{len(frame):,}\t{len(trimmed):,}\t{aggregation_ms:0.1f}\t{viewport_ms:0.1f}"
            )


def benchmark_basemaps() -> None:
    context = _build_context(5_000)
    frame = context.frame_for_resolution(context.base_resolution or 9, columns=["aucs"])
    frame = context.attach_geometries(frame)
    geojson = context.to_geojson(frame.head(5_000))
    print("\nBasemap render warm-up (5k hexes)")
    for option in basemap_options():
        style = option["value"]
        start = time.perf_counter()
        _ = create_choropleth(
            geojson=geojson,
            frame=frame.head(10_000),
            score_column="aucs",
            hover_columns=["aucs"],
            mapbox_token=None,
            map_style=style,
            transition_duration=0,
        )
        elapsed = (time.perf_counter() - start) * 1000
        print(f"{option['label']:<20} {elapsed:0.1f} ms")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sizes",
        type=int,
        nargs="*",
        default=[10_000, 100_000, 1_000_000],
        help="Dataset sizes (number of hexes) to benchmark",
    )
    parser.add_argument(
        "--basemap",
        action="store_true",
        help="Benchmark basemap render times",
    )
    args = parser.parse_args()
    benchmark_sizes(args.sizes)
    if args.basemap:
        benchmark_basemaps()


if __name__ == "__main__":
    main()
