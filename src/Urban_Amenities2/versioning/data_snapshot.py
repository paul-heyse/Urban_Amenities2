"""Data snapshot tracking utilities."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import List


@dataclass(slots=True)
class DataSnapshot:
    source_name: str
    version: str
    download_date: datetime
    file_hash: str

    def to_json(self) -> str:
        payload = asdict(self)
        payload["download_date"] = self.download_date.isoformat()
        return json.dumps(payload, sort_keys=True)

    @staticmethod
    def from_json(payload: str) -> "DataSnapshot":
        data = json.loads(payload)
        data["download_date"] = datetime.fromisoformat(data["download_date"])
        return DataSnapshot(**data)


def register_snapshot(snapshot: DataSnapshot, storage: Path) -> None:
    storage.parent.mkdir(parents=True, exist_ok=True)
    with storage.open("a", encoding="utf-8") as fp:
        fp.write(snapshot.to_json() + "\n")


def list_snapshots(storage: Path) -> List[DataSnapshot]:
    if not storage.exists():
        return []
    snapshots: List[DataSnapshot] = []
    for line in storage.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        snapshots.append(DataSnapshot.from_json(line))
    return snapshots
