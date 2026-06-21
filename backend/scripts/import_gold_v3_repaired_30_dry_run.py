"""Dry-run only import audit for repaired Gold V3 candidate recipes."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "backend" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from quality_gate_gold_recipes_30_candidate import evaluate as quality_evaluate  # noqa: E402


DEFAULT_INPUT = ROOT / "data" / "recipe_v2" / "gold_recipes_30_repaired_candidate.jsonl"
DEFAULT_REPORT_MD = ROOT / "reports" / "SPRINT_1_3D_GOLD_V3_IMPORT_DRY_RUN.md"
DEFAULT_REPORT_JSON = ROOT / "reports" / "SPRINT_1_3D_GOLD_V3_IMPORT_DRY_RUN.json"
FIXED_PILOT_IDS = set(range(256, 266))
SOURCE_MARKERS = ("povarenok", "поваренок", "source_url", "original_url", "http://", "https://", "http")
ENGLISH_PREFIX_RE = re.compile(
    r"^\s*(high protein|pro high protein|pro weight loss|pro small portion|pre-workout|post-workout|pro\s+[a-z][a-z\s-]*)\s*:",
    re.I,
)
REQUIRED_FIELDS = (
    "schema_version",
    "source_type",
    "title",
    "display_title",
    "normalized_title",
    "meal_type",
    "category",
    "tags",
    "image_prompt",
)
NUTRITION_FIELDS = ("kcal", "protein_g", "fat_g", "carbs_g")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def normalize(text: Any) -> str:
    value = re.sub(r"[^0-9a-zа-яё]+", " ", str(text or "").lower(), flags=re.I)
    return re.sub(r"\s+", " ", value).strip()


def recursive_text(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(recursive_text(v) for v in value.values())
    if isinstance(value, list):
        return " ".join(recursive_text(v) for v in value)
    return str(value or "")


def source_leakage(record: dict[str, Any]) -> bool:
    text = recursive_text(record).lower()
    return any(marker in text for marker in SOURCE_MARKERS)


def load_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    if not path.exists():
        return records, [f"missing_input:{path}"]
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            errors.append(f"line {index}: {exc}")
    return records, errors


def nutrition_core(record: dict[str, Any]) -> dict[str, Any]:
    return record.get("nutrition_per_serving") or record.get("nutrition") or {}


def check_record_contract(record: dict[str, Any], duplicate_titles: set[str]) -> list[str]:
    blockers: list[str] = []
    for field in REQUIRED_FIELDS:
        if record.get(field) in (None, "", []):
            blockers.append(f"{field}_missing")
    if len(record.get("ingredients") or []) < 3:
        blockers.append("ingredients_lt_3")
    if len(record.get("steps") or []) < 3:
        blockers.append("steps_lt_3")
    nutrition = nutrition_core(record)
    for field in NUTRITION_FIELDS:
        if nutrition.get(field) is None:
            blockers.append(f"nutrition_{field}_missing")
    if source_leakage(record):
        blockers.append("source_leakage")
    title = str(record.get("title") or "")
    if ENGLISH_PREFIX_RE.search(title) or "#" in title:
        blockers.append("title_garbage")
    if normalize(record.get("normalized_title") or record.get("title")) in duplicate_titles:
        blockers.append("duplicate_normalized_title")
    for image_field in ("hero_image_url", "image_url", "thumbnail_url"):
        if record.get(image_field):
            blockers.append(f"{image_field}_must_be_null")
    for item in record.get("ingredients") or []:
        if not (item.get("name") or item.get("display_name")):
            blockers.append("ingredient_name_missing")
        if item.get("amount") is None:
            blockers.append("ingredient_amount_missing")
        if not item.get("unit"):
            blockers.append("ingredient_unit_missing")
        if not (item.get("shopping_category_slug") or item.get("pantry_category_slug")):
            blockers.append("ingredient_shopping_category_missing")
    for step_index, step in enumerate(record.get("steps") or [], start=1):
        if not (step.get("text") or step.get("instruction")):
            blockers.append(f"step_{step_index}_text_missing")
    return sorted(set(blockers))


def evaluate_file_contract(records: list[dict[str, Any]], json_errors: list[str]) -> dict[str, Any]:
    title_counts = Counter(normalize(record.get("normalized_title") or record.get("title")) for record in records)
    duplicate_titles = {title for title, count in title_counts.items() if title and count > 1}
    items = []
    blocker_counts: Counter[str] = Counter(json_errors)
    fixed_id_conflicts = []
    for index, record in enumerate(records, start=1):
        blockers = check_record_contract(record, duplicate_titles)
        blocker_counts.update(blockers)
        recipe_id = record.get("id")
        if recipe_id in FIXED_PILOT_IDS:
            fixed_id_conflicts.append({"index": index, "id": recipe_id, "title": record.get("title")})
        items.append(
            {
                "index": index,
                "title": record.get("title"),
                "normalized_title": normalize(record.get("normalized_title") or record.get("title")),
                "blockers": blockers,
                "ingredients_count": len(record.get("ingredients") or []),
                "steps_count": len(record.get("steps") or []),
            }
        )
    return {
        "record_count": len(records),
        "valid_json": not json_errors,
        "json_errors": json_errors,
        "fixed_id_conflicts": fixed_id_conflicts,
        "items": items,
        "blocker_counts": dict(blocker_counts),
        "top_blockers": blocker_counts.most_common(10),
        "hard_fail": len(json_errors) + sum(1 for item in items if item["blockers"]) + len(fixed_id_conflicts),
    }


def simulated_ids(current_max_id: int | None, count: int) -> list[int]:
    if current_max_id is None:
        return []
    return list(range(current_max_id + 1, current_max_id + count + 1))


def find_duplicate_risks(records: list[dict[str, Any]], existing_rows: list[dict[str, Any]]) -> dict[str, Any]:
    batch_titles = {normalize(record.get("title")) for record in records if record.get("title")}
    batch_normalized = {
        normalize(record.get("normalized_title") or record.get("title"))
        for record in records
        if record.get("normalized_title") or record.get("title")
    }
    title_matches = []
    normalized_matches = []
    close_matches = []
    for row in existing_rows:
        title = normalize(row.get("title"))
        normalized_title = normalize(row.get("normalized_title") or row.get("title"))
        if title and title in batch_titles:
            title_matches.append(row)
        if normalized_title and normalized_title in batch_normalized:
            normalized_matches.append(row)
        if title and title in batch_normalized:
            close_matches.append(row)
    return {
        "duplicate_title_matches": title_matches,
        "duplicate_normalized_matches": normalized_matches,
        "duplicate_close_matches": close_matches,
    }


def collect_db_snapshot(records: list[dict[str, Any]], database_url: str | None = None) -> dict[str, Any]:
    database_url = database_url or os.getenv("DATABASE_URL") or "postgresql://aifood:aifood@localhost:5432/aifood"
    try:
        from sqlalchemy import create_engine, inspect, text
    except Exception as exc:  # pragma: no cover - depends on local env
        return {
            "db_available": False,
            "reason": f"sqlalchemy_unavailable:{exc}",
            "current_max_id": None,
            "simulated_ids": [],
            "recipes_total": None,
        }

    try:
        engine = create_engine(database_url, future=True)
        with engine.connect() as conn:
            inspector = inspect(conn)
            tables = set(inspector.get_table_names())
            columns = {
                table: [column["name"] for column in inspector.get_columns(table)]
                for table in ("recipes", "recipe_ingredients", "recipe_steps")
                if table in tables
            }
            if "recipes" not in tables:
                raise RuntimeError("recipes table not found")
            recipe_columns = set(columns.get("recipes") or [])
            title_select = "normalized_title" if "normalized_title" in recipe_columns else "title"
            rows = conn.execute(
                text(f"select id, title, {title_select} as normalized_title from recipes")
            ).mappings().all()
            max_id = conn.execute(text("select coalesce(max(id), 0) from recipes")).scalar_one()
            total = conn.execute(text("select count(*) from recipes")).scalar_one()
        existing_rows = [dict(row) for row in rows]
        duplicate_report = find_duplicate_risks(records, existing_rows)
        return {
            "db_available": True,
            "recipes_total": int(total),
            "current_max_id": int(max_id),
            "simulated_ids": simulated_ids(int(max_id), len(records)),
            "table_columns": columns,
            "missing_expected_tables": [
                table for table in ("recipes", "recipe_ingredients", "recipe_steps") if table not in tables
            ],
            **duplicate_report,
        }
    except Exception as exc:
        return {
            "db_available": False,
            "reason": str(exc),
            "current_max_id": None,
            "simulated_ids": [],
            "recipes_total": None,
        }


def run_dry_run(
    input_path: Path = DEFAULT_INPUT,
    report_md: Path = DEFAULT_REPORT_MD,
    report_json: Path = DEFAULT_REPORT_JSON,
    *,
    database_url: str | None = None,
    db_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    records, json_errors = load_jsonl(input_path)
    quality = quality_evaluate(records, json_errors)
    file_contract = evaluate_file_contract(records, json_errors)
    db = db_snapshot if db_snapshot is not None else collect_db_snapshot(records, database_url)
    duplicate_count = sum(
        len(db.get(key) or [])
        for key in ("duplicate_title_matches", "duplicate_normalized_matches", "duplicate_close_matches")
    )
    db_blocked = bool(db.get("db_available") and duplicate_count)
    blocked = (
        len(records) != 30
        or quality.get("hard_fail") != 0
        or quality.get("valid_for_import") != 30
        or file_contract["hard_fail"] != 0
        or db_blocked
    )
    readiness = "ready" if not blocked and db.get("db_available") else "partial" if not blocked else "blocked"
    partial_reasons = []
    if not db.get("db_available"):
        partial_reasons.append("DB duplicate/id simulation skipped")
    report = {
        "generated_at": now(),
        "input": rel(input_path),
        "apply": False,
        "dry_run": True,
        "db_writes": 0,
        "records": len(records),
        "quality_gate": {
            "valid_for_import": quality.get("valid_for_import"),
            "hard_fail": quality.get("hard_fail"),
            "top_blockers": quality.get("top_blockers"),
        },
        "file_contract": file_contract,
        "db": db,
        "db_available": bool(db.get("db_available")),
        "current_max_id": db.get("current_max_id"),
        "simulated_ids": db.get("simulated_ids") or [],
        "duplicate_risks": {
            "title": db.get("duplicate_title_matches") or [],
            "normalized_title": db.get("duplicate_normalized_matches") or [],
            "close_title": db.get("duplicate_close_matches") or [],
        },
        "fixed_id_conflicts": file_contract["fixed_id_conflicts"],
        "blocked": blocked,
        "readiness": readiness,
        "partial_reasons": partial_reasons,
        "blockers": file_contract["top_blockers"],
        "notes": [
            "Apply is disabled in Sprint 1.3D.",
            "Recipes 256-265 are reserved for the Gold V3 pilot and are not reused.",
            "Image URLs must remain null until photos are created in a future sprint.",
        ],
    }
    report_json.parent.mkdir(parents=True, exist_ok=True)
    report_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_md.write_text(render_import_report(report), encoding="utf-8")
    return report


def render_import_report(report: dict[str, Any]) -> str:
    db = report["db"]
    duplicate_risks = report["duplicate_risks"]
    lines = [
        "# Sprint 1.3D Gold V3 Import Dry-Run",
        "",
        f"Generated: `{report['generated_at']}`",
        f"Input: `{report['input']}`",
        f"apply: `{report['apply']}`",
        f"db_writes: `{report['db_writes']}`",
        f"records: `{report['records']}`",
        f"valid_for_import: `{report['quality_gate']['valid_for_import']}`",
        f"hard_fail: `{report['quality_gate']['hard_fail']}`",
        f"blocked: `{report['blocked']}`",
        f"readiness: `{report['readiness']}`",
        "",
        "## DB",
        "",
        f"db_available: `{report['db_available']}`",
        f"recipes_total: `{db.get('recipes_total')}`",
        f"current_max_id: `{report['current_max_id']}`",
        f"simulated_ids: `{report['simulated_ids']}`",
        f"partial_reasons: `{report['partial_reasons']}`",
        "",
        "## Duplicate Risks",
        "",
        f"title: `{len(duplicate_risks['title'])}`",
        f"normalized_title: `{len(duplicate_risks['normalized_title'])}`",
        f"close_title: `{len(duplicate_risks['close_title'])}`",
        "",
        "## Fixed ID Conflicts",
        "",
        f"256-265 reused: `{bool(report['fixed_id_conflicts'])}`",
        "",
        "## Top Blockers",
        "",
    ]
    if report["blockers"]:
        lines.extend(f"- {code}: `{count}`" for code, count in report["blockers"])
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--report-md", default=str(DEFAULT_REPORT_MD))
    parser.add_argument("--report-json", default=str(DEFAULT_REPORT_JSON))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.apply:
        print("Apply is intentionally disabled in Sprint 1.3D", file=sys.stderr)
        return 2
    report = run_dry_run(Path(args.input), Path(args.report_md), Path(args.report_json))
    print(f"Wrote {args.report_md}")
    return 0 if not report["blocked"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
