from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class SnapshotRecord:
    source: str
    url: str
    sha256: str
    timestamp: str

    def to_json(self) -> str:
        return json.dumps(self.__dict__, sort_keys=True)


class SnapshotRegistry:
    def __init__(self, path: Path = Path("data/snapshots.jsonl")):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.touch()

    def record_snapshot(self, source: str, url: str, data: bytes) -> SnapshotRecord:
        sha = hashlib.sha256(data).hexdigest()
        latest = self.latest_for(source)
        if latest and latest.sha256 == sha:
            return latest
        record = SnapshotRecord(source=source, url=url, sha256=sha, timestamp=datetime.utcnow().isoformat())
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(record.to_json() + "\n")
        return record

    def list_snapshots(self) -> list[SnapshotRecord]:
        records: list[SnapshotRecord] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                payload = json.loads(line)
                records.append(SnapshotRecord(**payload))
        return records

    def latest_for(self, source: str) -> SnapshotRecord | None:
        records = [record for record in self.list_snapshots() if record.source == source]
        return records[-1] if records else None

    def has_changed(self, source: str, data: bytes) -> bool:
        sha = hashlib.sha256(data).hexdigest()
        latest = self.latest_for(source)
        return latest is None or latest.sha256 != sha

    def list_json(self) -> list[dict[str, str]]:
        return [record.__dict__ for record in self.list_snapshots()]


__all__ = ["SnapshotRegistry", "SnapshotRecord"]
