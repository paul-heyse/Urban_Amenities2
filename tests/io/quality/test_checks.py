from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from Urban_Amenities2.io.quality import checks


def test_coverage_check_counts() -> None:
    frame = pd.DataFrame({"hex_id": ["a", "a", "b"], "poi_id": [1, 2, 3]})
    metrics = checks.coverage_check(frame)
    assert metrics == {"hex_count": 2, "avg_pois_per_hex": pytest.approx(1.5)}


def test_completeness_handles_missing_columns() -> None:
    frame = pd.DataFrame({"name": ["A"], "hex_id": ["h"]})
    metrics = checks.completeness_check(frame, ["name", "hex_id", "aucstype"])
    assert metrics["name"] == 1.0
    assert metrics["hex_id"] == 1.0
    assert metrics["aucstype"] == 0.0


def test_validity_check_bounds() -> None:
    frame = pd.DataFrame({"lat": [45.0, 100.0], "lon": [0.0, 0.0]})
    metrics = checks.validity_check(frame)
    assert metrics["within_bounds"] == pytest.approx(0.5)


def test_validity_empty_frame() -> None:
    frame = pd.DataFrame(columns=["lat", "lon"])
    metrics = checks.validity_check(frame)
    assert metrics["within_bounds"] == 1.0


def test_consistency_with_enrichment() -> None:
    pois = pd.DataFrame(
        {
            "poi_id": ["a", "b"],
            "dedupe_weight": [1.0, None],
        }
    )
    enrichment = pd.DataFrame({"poi_id": ["a"], "extra": [1]})
    metrics = checks.consistency_check(pois, enrichment=enrichment)
    assert metrics["dedupe_weight_non_null"] == pytest.approx(0.5)
    assert metrics["enrichment_join_rate"] == pytest.approx(0.5)


def test_generate_report_writes_json(tmp_path: Path) -> None:
    pois = pd.DataFrame(
        {
            "poi_id": ["a"],
            "hex_id": ["hex"],
            "name": ["Place"],
            "aucstype": ["park"],
            "lat": [45.0],
            "lon": [7.0],
        }
    )
    report = checks.generate_report(pois, output_dir=tmp_path)
    path = tmp_path / "pois_quality.json"
    assert path.exists()
    stored = json.loads(path.read_text(encoding="utf-8"))
    assert stored == report
    assert report["coverage"]["hex_count"] == 1
