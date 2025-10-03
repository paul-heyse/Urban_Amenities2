"""Generate synthetic AUCS outputs for UI development."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from Urban_Amenities2.ui.hexes import HexGeometryCache

SUBSCORES = ["EA", "LCA", "MUHAA", "JEA", "MORR", "CTE", "SOU"]
STATES = ["CO", "UT", "ID"]
METROS = ["Denver", "Salt Lake City", "Boise", "Fort Collins"]
COUNTIES = ["Denver County", "Salt Lake County", "Ada County", "Larimer County"]


def random_hex(resolution: int = 8) -> str:
    import h3

    base = h3.latlng_to_cell(np.random.uniform(37, 43), np.random.uniform(-114, -104), resolution)
    return base


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/outputs"),
        help="Directory for generated Parquet files",
    )
    parser.add_argument("--count", type=int, default=1000, help="Number of hexes to generate")
    args = parser.parse_args()

    rng = np.random.default_rng(1234)
    hex_cache = HexGeometryCache()

    hex_ids = [random_hex() for _ in range(args.count)]
    hex_cache.ensure_geometries(hex_ids)

    scores = pd.DataFrame({"hex_id": hex_ids})
    for subscore in SUBSCORES:
        scores[subscore] = rng.uniform(0, 100, size=args.count)
    scores["aucs"] = scores[SUBSCORES].mean(axis=1)
    scores["state"] = rng.choice(STATES, size=args.count)
    scores["metro"] = rng.choice(METROS, size=args.count)
    scores["county"] = rng.choice(COUNTIES, size=args.count)

    metadata = scores[["hex_id", "state", "metro", "county"]].copy()

    output_dir = args.output
    output_dir.mkdir(parents=True, exist_ok=True)
    scores.to_parquet(output_dir / "scores.parquet", index=False)
    metadata.to_parquet(output_dir / "metadata.parquet", index=False)
    print(f"Wrote dataset to {output_dir}")


if __name__ == "__main__":
    main()
