from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

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

    def fake_ingest_places(
        src: Path, crosswalk_path: Path, bbox: object, output_path: Path
    ) -> None:
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


def test_ingest_gtfs_invokes_static_and_realtime_ingestors(
    cli_runner: CliRunner, tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    output_dir = tmp_path / "gtfs"
    calls: dict[str, Any] = {}

    monkeypatch.setattr(
        "Urban_Amenities2.cli.main.load_registry",
        lambda: [SimpleNamespace(name="Metro Transit", realtime_urls=["http://example.com"])],
    )

    class DummyStaticIngestor:
        def ingest(self, agency: object, output_dir: Path) -> list[Path]:
            calls["static"] = {"agency": agency.name, "output": output_dir}
            output_dir.mkdir(parents=True, exist_ok=True)
            return [output_dir / "feed.zip"]

    class DummyRealtimeIngestor:
        def ingest(self, agency: object) -> Path:
            calls["realtime"] = agency.name
            return output_dir / "realtime.json"

    monkeypatch.setattr("Urban_Amenities2.cli.main.GTFSStaticIngestor", lambda: DummyStaticIngestor())
    monkeypatch.setattr(
        "Urban_Amenities2.cli.main.GTFSRealtimeIngestor", lambda: DummyRealtimeIngestor()
    )

    result = cli_runner.invoke(
        app,
        ["ingest", "gtfs", "Metro Transit", "--output-dir", str(output_dir)],
    )

    assert result.exit_code == 0
    assert "Static GTFS outputs" in result.stdout
    assert "Realtime metrics" in result.stdout
    assert calls["static"] == {"agency": "Metro Transit", "output": output_dir}
    assert calls["realtime"] == "Metro Transit"


def test_ingest_gtfs_missing_agency(cli_runner: CliRunner, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr("Urban_Amenities2.cli.main.load_registry", lambda: [])

    result = cli_runner.invoke(app, ["ingest", "gtfs", "Unknown Agency"])

    assert result.exit_code == 1
    assert "not found" in result.stdout


def test_ingest_unknown_subcommand(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(app, ["ingest", "unknown"])

    assert result.exit_code != 0
    combined = result.stdout + result.stderr
    assert "No such command" in combined


def test_ingest_overture_places_missing_argument(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(app, ["ingest", "overture-places"])

    assert result.exit_code != 0
    combined = result.stdout + result.stderr
    assert "Missing argument" in combined
