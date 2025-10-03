from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import pytest
from typer.testing import CliRunner

from Urban_Amenities2.cli.main import app
from Urban_Amenities2.config.loader import load_params
from Urban_Amenities2.versioning.data_snapshot import (
    DataSnapshot,
    list_snapshots,
    register_snapshot,
)
from Urban_Amenities2.versioning.manifest import (
    RunManifest,
    append_manifest,
    create_run_manifest,
    get_manifest,
    list_manifests,
)


def test_create_run_manifest(tmp_path: Path) -> None:
    params_path = Path("configs/params_default.yml")
    _, param_hash = load_params(params_path)
    storage = tmp_path / "runs.jsonl"
    manifest = create_run_manifest(param_hash, [], git_commit="abc123", storage=storage)
    assert manifest.param_hash == param_hash
    stored = list_manifests(storage)
    assert stored[0].run_id == manifest.run_id


def test_cli_config_validate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["config", "validate", "configs/params_default.yml"])
    assert result.exit_code == 0


def test_cli_run_init(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runner = CliRunner()
    monkeypatch.setattr("Urban_Amenities2.cli.main.RUN_STORAGE", tmp_path / "runs.jsonl")
    result = runner.invoke(
        app, ["run", "init", "configs/params_default.yml", "--git-commit", "abc"]
    )
    assert result.exit_code == 0
    list_result = runner.invoke(app, ["run", "list"])
    assert "hash" in list_result.stdout or "run" in list_result.stdout


def test_snapshot_registration(tmp_path: Path) -> None:
    storage = tmp_path / "snapshots.jsonl"
    snapshot = DataSnapshot(
        source_name="Overture",
        version="2024-02-01",
        download_date=pd.Timestamp("2024-02-15"),
        file_hash="abc123",
    )
    register_snapshot(snapshot, storage)
    snapshots = list_snapshots(storage)
    assert snapshots[0].source_name == "Overture"


def test_run_manifest_append_and_lookup(tmp_path: Path) -> None:
    storage = tmp_path / "runs.jsonl"
    manifest = RunManifest(
        run_id="run-1",
        timestamp=datetime.now(UTC),
        param_hash="abc",
        data_snapshot_ids=["snap-1"],
        git_commit="deadbeef",
    )
    append_manifest(manifest, storage)
    listed = list_manifests(storage)
    assert listed[0].run_id == "run-1"
    fetched = get_manifest("run-1", storage)
    assert fetched is not None
    assert fetched.git_commit == "deadbeef"


def test_list_manifests_missing_file(tmp_path: Path) -> None:
    storage = tmp_path / "absent.jsonl"
    assert list_manifests(storage) == []
