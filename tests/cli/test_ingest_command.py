from __future__ import annotations

from pathlib import Path

from pytest import MonkeyPatch
from typer.testing import CliRunner

from Urban_Amenities2.cli.main import app


def test_ingest_overture_places_invokes_ingestor(
    cli_runner: CliRunner, tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    source = tmp_path / "source.parquet"
    source.write_text("dummy", encoding="utf-8")
    crosswalk = tmp_path / "crosswalk.txt"
    crosswalk.write_text("crosswalk", encoding="utf-8")
    output = tmp_path / "output.parquet"
    calls: dict[str, Any] = {}

    def fake_ingest_places(src: Path, crosswalk_path: Path, bbox: object, output_path: Path) -> None:
        calls["arguments"] = {
            "src": src,
            "crosswalk": crosswalk_path,
            "bbox": bbox,
            "output": output_path,
        }
        output_path.write_text("data", encoding="utf-8")

    monkeypatch.setattr("Urban_Amenities2.cli.main.ingest_places", fake_ingest_places)

    result = cli_runner.invoke(
        app,
        [
            "ingest",
            "overture-places",
            str(source),
            "--crosswalk",
            str(crosswalk),
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0
    assert "Wrote POIs" in result.stdout
    assert calls["arguments"]["src"] == source
    assert output.exists()


def test_ingest_overture_places_invalid_bbox(cli_runner: CliRunner, tmp_path: Path) -> None:
    source = tmp_path / "source.parquet"
    source.write_text("dummy", encoding="utf-8")
    result = cli_runner.invoke(
        app,
        ["ingest", "overture-places", str(source), "--bbox", "1,2,3"],
    )
    assert result.exit_code != 0
    assert "bbox must be" in result.output
