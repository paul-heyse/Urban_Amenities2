"""Run manifest generation and storage."""
from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional


@dataclass(slots=True)
class RunManifest:
    run_id: str
    timestamp: datetime
    param_hash: str
    data_snapshot_ids: List[str]
    git_commit: Optional[str]

    def to_json(self) -> str:
        payload = asdict(self)
        payload["timestamp"] = self.timestamp.isoformat()
        return json.dumps(payload, sort_keys=True)

    @staticmethod
    def from_json(payload: str) -> "RunManifest":
        data = json.loads(payload)
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return RunManifest(**data)


def create_run_manifest(
    param_hash: str,
    data_snapshot_ids: Iterable[str],
    git_commit: Optional[str],
    storage: Path,
) -> RunManifest:
    run = RunManifest(
        run_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        param_hash=param_hash,
        data_snapshot_ids=list(data_snapshot_ids),
        git_commit=git_commit,
    )
    append_manifest(run, storage)
    return run


def append_manifest(manifest: RunManifest, storage: Path) -> None:
    storage.parent.mkdir(parents=True, exist_ok=True)
    with storage.open("a", encoding="utf-8") as fp:
        fp.write(manifest.to_json() + "\n")


def list_manifests(storage: Path) -> List[RunManifest]:
    if not storage.exists():
        return []
    manifests: List[RunManifest] = []
    for line in storage.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        manifests.append(RunManifest.from_json(line))
    return manifests


def get_manifest(run_id: str, storage: Path) -> Optional[RunManifest]:
    for manifest in list_manifests(storage):
        if manifest.run_id == run_id:
            return manifest
    return None
