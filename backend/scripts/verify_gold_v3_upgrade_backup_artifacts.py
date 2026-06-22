"""Verify Gold V3 upgrade backup artifact directory."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REPORT_MD = ROOT / "reports" / "SPRINT_1_3H_GOLD_V3_BACKUP_ARTIFACTS_VERIFY.md"
REPORT_JSON = ROOT / "reports" / "SPRINT_1_3H_GOLD_V3_BACKUP_ARTIFACTS_VERIFY.json"
EXPECTED_IDS = [2, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255]
REQUIRED_FILES = ("MANIFEST.md", "manifest.json", "recipes.jsonl", "recipe_ingredients.jsonl", "recipe_steps.jsonl", "rollback_manifest.json", "verification_report.md")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def tracked_files() -> set[str]:
    try:
        output = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True)
    except Exception:
        return set()
    return {str((ROOT / line.strip()).resolve()) for line in output.splitlines() if line.strip()}


def verify(backup_dir: Path, write_reports: bool = True) -> dict[str, Any]:
    backup_dir = backup_dir.resolve()
    blockers = []
    if not backup_dir.exists():
        blockers.append("backup_dir_missing")
    files = {name: backup_dir / name for name in REQUIRED_FILES}
    for name, path in files.items():
        if not path.exists():
            blockers.append(f"{name}_missing")

    manifest = json.loads(files["manifest.json"].read_text(encoding="utf-8")) if files["manifest.json"].exists() else {}
    rollback = json.loads(files["rollback_manifest.json"].read_text(encoding="utf-8")) if files["rollback_manifest.json"].exists() else {}
    recipes = load_jsonl(files["recipes.jsonl"]) if files["recipes.jsonl"].exists() else []
    ingredients = load_jsonl(files["recipe_ingredients.jsonl"]) if files["recipe_ingredients.jsonl"].exists() else []
    steps = load_jsonl(files["recipe_steps.jsonl"]) if files["recipe_steps.jsonl"].exists() else []
    recipe_ids = sorted(int(row["id"]) for row in recipes if row.get("id") is not None)
    if len(recipes) != 30:
        blockers.append("recipes_count_not_30")
    if recipe_ids != EXPECTED_IDS:
        blockers.append("recipe_ids_mismatch")
    if not ingredients:
        blockers.append("recipe_ingredients_empty")
    if not steps:
        blockers.append("recipe_steps_empty")
    relation_dir = backup_dir / "relation_tables"
    if not relation_dir.exists():
        blockers.append("relation_tables_dir_missing")
    if (manifest.get("relation_tables") or {}).get("recipe_explanations", {}).get("rows", 0) > 0:
        if not (relation_dir / "recipe_explanations.jsonl").exists():
            blockers.append("recipe_explanations_backup_missing")
    if rollback.get("upgrade_apply_allowed") is not False:
        blockers.append("rollback_manifest_allows_apply")
    tracked = tracked_files()
    tracked_hits = [
        str(path)
        for path in backup_dir.rglob("*")
        if path.is_file() and str(path.resolve()) in tracked
    ]
    if tracked_hits:
        blockers.append("backup_files_tracked_by_git")
    report = {
        "backup_dir": str(backup_dir),
        "ok": not blockers,
        "blockers": blockers,
        "recipes_count": len(recipes),
        "recipe_ids": recipe_ids,
        "recipe_ingredients_count": len(ingredients),
        "recipe_steps_count": len(steps),
        "relation_tables_exists": relation_dir.exists(),
        "tracked_hits": tracked_hits,
        "manifest_backup_id": manifest.get("backup_id"),
    }
    if write_reports:
        REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
        REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        REPORT_MD.write_text(render(report), encoding="utf-8")
    return report


def render(report: dict[str, Any]) -> str:
    lines = [
        "# Sprint 1.3H Gold V3 Backup Artifacts Verify",
        "",
        f"backup_dir: `{report['backup_dir']}`",
        f"ok: `{report['ok']}`",
        f"blockers: `{report['blockers']}`",
        f"recipes_count: `{report['recipes_count']}`",
        f"recipe_ingredients_count: `{report['recipe_ingredients_count']}`",
        f"recipe_steps_count: `{report['recipe_steps_count']}`",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backup-dir", required=True)
    args = parser.parse_args(argv)
    report = verify(Path(args.backup_dir))
    print(f"Wrote {REPORT_MD}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
