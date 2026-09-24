from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class BackupManifest:
    git_commit: str
    alembic_revision: str
    cutover_state: str
    reconciliation_report: str
    object_counts: dict[str, int]


def write_local_backup(path: Path, manifest: BackupManifest, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps({"manifest": asdict(manifest), "payload": payload}, sort_keys=True), encoding="utf-8")


def restore_local_backup(path: Path) -> tuple[BackupManifest, dict[str, Any]]:
    document = json.loads(path.read_text(encoding="utf-8"))
    return BackupManifest(**document["manifest"]), document["payload"]
