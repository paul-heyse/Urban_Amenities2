import json
from pathlib import Path

import pandas as pd
from typer.testing import CliRunner

from Urban_Amenities2.cli.main import app


def test_routing_compute_skims_cli(tmp_path: Path) -> None:
    origins = tmp_path / "origins.csv"
    origins.write_text("id,lat,lon\nA,39.0,-104.0\n", encoding="utf-8")
    destinations = tmp_path / "destinations.csv"
    destinations.write_text("id,lat,lon\nB,39.1,-104.1\n", encoding="utf-8")
    output = tmp_path / "skims.parquet"

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "routing",
            "compute-skims",
            str(origins),
            str(destinations),
            "--output-path",
            str(output),
        ],
    )
    assert result.exit_code == 0, result.output
    assert output.exists()


def test_data_list_snapshots_cli(tmp_path: Path) -> None:
    registry = tmp_path / "snap.jsonl"
    record = {"source": "test", "url": "http://example.com", "sha256": "abc", "timestamp": "2024"}
    registry.write_text(json.dumps(record) + "\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(app, ["data", "list-snapshots", "--path", str(registry)])
    assert result.exit_code == 0, result.output
    assert "test" in result.output


def test_score_ea_cli(tmp_path: Path) -> None:
    pois = pd.DataFrame(
        {
            "poi_id": ["p1"],
            "aucstype": ["grocery"],
            "quality": [1.0],
            "brand": ["Brand"],
            "name": ["Store"],
        }
    )
    pois_path = tmp_path / "pois.parquet"
    pois.to_parquet(pois_path)

    accessibility = pd.DataFrame(
        {
            "poi_id": ["p1"],
            "origin_hex": ["hex1"],
            "weight": [1.0],
            "mode": ["car"],
            "period": ["AM"],
        }
    )
    accessibility_path = tmp_path / "access.parquet"
    accessibility.to_parquet(accessibility_path)

    output = tmp_path / "ea.parquet"

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "score",
            "ea",
            str(pois_path),
            str(accessibility_path),
            "--output",
            str(output),
        ],
    )
    assert result.exit_code == 0, result.output
    assert output.exists()


def test_aggregate_and_export_cli(tmp_path: Path) -> None:
    subscores = pd.DataFrame(
        {
            "hex_id": ["hex1", "hex2"],
            "ea": [60.0, 70.0],
            "health": [50.0, 80.0],
            "contributors": [
                {"grocery": [{"poi_id": "p1", "name": "Store", "contribution": 1.2}]},
                {},
            ],
        }
    )
    subscores_path = tmp_path / "subscores.parquet"
    subscores.to_parquet(subscores_path)

    output = tmp_path / "aucs.parquet"
    explain = tmp_path / "explain.parquet"
    report = tmp_path / "report.html"
    weights = json.dumps({"ea": 0.7, "health": 0.3})

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "aggregate",
            str(subscores_path),
            "--weights",
            weights,
            "--output",
            str(output),
            "--explainability-output",
            str(explain),
            "--report-path",
            str(report),
        ],
    )
    assert result.exit_code == 0, result.output
    aggregated = pd.read_parquet(output)
    assert "aucs" in aggregated.columns
    assert explain.exists()
    assert report.exists()

    show_result = runner.invoke(app, ["show", "--hex", "hex1", "--scores", str(output)])
    assert show_result.exit_code == 0, show_result.output

    export_path = tmp_path / "aucs.geojson"
    export_result = runner.invoke(app, ["export", str(export_path), "--scores", str(output)])
    assert export_result.exit_code == 0, export_result.output
    geojson = json.loads(export_path.read_text())
    assert geojson["features"], "GeoJSON export should include features"
    for feature in geojson["features"]:
        properties = feature["properties"]
        assert isinstance(properties, dict)
        for key, value in properties.items():
            assert isinstance(key, str)
            assert not isinstance(value, (pd.Series, pd.Index))
