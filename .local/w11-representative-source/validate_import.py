from __future__ import annotations

import json
import sqlite3
from pathlib import Path


base = Path(__file__).parent
first = json.loads((base / "apply-1.report.json").read_text(encoding="utf-8"))
second = json.loads((base / "apply-2.report.json").read_text(encoding="utf-8"))
recreated = json.loads((base / "apply-recreate.report.json").read_text(encoding="utf-8"))

for report in (first, second, recreated):
    assert report["unresolved_fatal_conflicts"] == 0
    assert report["collisions"] == []
assert first["target_records_created"] == 19
assert second["target_records_created"] == 0
assert recreated["target_records_created"] == 19
assert first["target_counts"] == recreated["target_counts"]

connection = sqlite3.connect(base / "target-2.sqlite")
tables = {row[0] for row in connection.execute("select name from sqlite_master where type='table'")}
assert connection.execute("select version_num from alembic_version").fetchone()[0] == "20260927_0019"
assert connection.execute("select count(*) from core_accounts").fetchone()[0] == 4
assert connection.execute("select count(*) from core_persons").fetchone()[0] == 4
assert connection.execute("select count(*) from food_profiles").fetchone()[0] == 3
assert connection.execute("select count(*) from food_profile_reconfirmations").fetchone()[0] == 4
assert "admin_sessions" not in tables
assert "notification_deliveries" not in tables
connection.close()

print("POST_IMPORT_SAFETY=PASS")
print("POST_IMPORT_INTEGRITY=PASS")
print("TARGET_COUNTS=" + json.dumps(recreated["target_counts"], sort_keys=True))
