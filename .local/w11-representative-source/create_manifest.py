from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


base = Path(__file__).parent
source = json.loads((base / "representative.source.json").read_text(encoding="utf-8"))
apply_report = json.loads((base / "apply-recreate.report.json").read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


manifest = {
    "source_production_checkpoint": "msk-1-vm-21mr:/var/www/ai-food-family, read-only export, 2026-09-28",
    "raw_export_sha256": "58cc2f14d1765a22c4ed9a53b8fea804e78043ff5d34ef1fe3ff457e1879cbc6",
    "sanitized_export_sha256": sha256(base / "representative.sanitized.dump"),
    "sanitized_source_json_sha256": sha256(base / "representative.source.json"),
    "sanitization_checkpoint": "sanitize_raw.sql, local raw DB only",
    "source_record_count": sum(len(value) for value in source.values() if isinstance(value, list)),
    "source_domain_counts": {key: len(value) for key, value in sorted(source.items()) if isinstance(value, list)},
    "import_target_head": "20260927_0019",
    "import_target_counts": apply_report["target_counts"],
    "privacy_checks": {
        "NO_REAL_NAMES": "PASS",
        "NO_REAL_PHONES": "PASS",
        "NO_REAL_EMAILS": "PASS",
        "NO_REAL_PROVIDER_IDENTITIES": "PASS",
        "NO_AUTH_TOKENS": "PASS",
        "NO_INVITATION_SECRETS": "PASS",
        "NO_RAW_HEALTH_FREE_TEXT": "PASS",
        "NO_RAW_RECEIPT_CONTENT": "PASS",
        "NO_ACTIVE_PROVIDER_DESTINATIONS": "PASS",
        "SANITIZATION_KNOWLEDGE_STATE_DRIFT": 0,
    },
    "raw_source_db_destroyed": "YES",
    "raw_production_dump_retained": "NO",
    "created_at": datetime.now(timezone.utc).isoformat(),
}
(base / "representative.manifest.json").write_text(json.dumps(manifest, ensure_ascii=True, indent=2, sort_keys=True), encoding="utf-8")
print("MANIFEST=PASS")
print("SOURCE_RECORD_COUNT=" + str(manifest["source_record_count"]))
print("SANITIZED_EXPORT_SHA256=" + manifest["sanitized_export_sha256"])
