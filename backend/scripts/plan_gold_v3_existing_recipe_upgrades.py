"""Read-only upgrade planning for Gold V3 candidates that duplicate existing recipes."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "backend" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import audit_gold_v3_repaired_30_duplicates as duplicates  # noqa: E402


INPUT = ROOT / "data" / "recipe_v2" / "gold_recipes_30_repaired_candidate.jsonl"
DUPLICATE_REPORT_JSON = ROOT / "reports" / "SPRINT_1_3D_GOLD_V3_DUPLICATE_RESOLUTION.json"
REPORTS = ROOT / "reports"
REPORT_MD = REPORTS / "SPRINT_1_3E_GOLD_V3_UPGRADE_PLAN.md"
REPORT_JSON = REPORTS / "SPRINT_1_3E_GOLD_V3_UPGRADE_PLAN.json"
PLAN_JSON = ROOT / "data" / "recipe_v2" / "gold_v3_existing_recipe_upgrade_plan.json"
SOURCE_MARKERS = ("source_url", "original_url", "http://", "https://", "http", "povarenok", "поваренок")
RELATION_TABLE_HINTS = (
    "meal_plan",
    "planned_meal",
    "menu",
    "shopping",
    "favorite",
    "history",
    "cooked",
    "user_recipe",
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def has_source_leakage(value: Any) -> bool:
    text = json.dumps(value, ensure_ascii=False).lower()
    return any(marker in text for marker in SOURCE_MARKERS)


def load_duplicate_report(
    candidates: list[dict[str, Any]] | None = None,
    existing: list[duplicates.ExistingRecipe] | None = None,
    duplicate_report_path: Path = DUPLICATE_REPORT_JSON,
) -> dict[str, Any]:
    if duplicate_report_path.exists() and candidates is None and existing is None:
        return json.loads(duplicate_report_path.read_text(encoding="utf-8"))
    return duplicates.audit(candidates, existing, write_reports=False)


def load_candidates_by_index(candidates: list[dict[str, Any]] | None = None) -> dict[int, dict[str, Any]]:
    records = candidates if candidates is not None else duplicates.load_candidates(INPUT)
    return {index: record for index, record in enumerate(records, start=1)}


def fields_to_replace(candidate: dict[str, Any], match: dict[str, Any]) -> list[str]:
    fields = ["ingredients", "steps", "nutrition", "tags", "source_type_gold_v3_metadata", "shopping_readiness"]
    if candidate.get("title") and candidate.get("title") != match.get("db_title"):
        fields.insert(0, "title/display_title")
    if candidate.get("meal_type") != match.get("db_meal_type") or candidate.get("category") != match.get("db_category"):
        fields.append("meal_type/category")
    return fields


def fields_to_preserve(match: dict[str, Any]) -> list[str]:
    fields = [
        "id",
        "created_at",
        "user relations/history/favorites/menu references",
        "existing image URLs",
        "source metadata remains internal only",
    ]
    if match.get("db_has_images"):
        fields.append("image_url/hero_image_url/thumbnail_url")
    return fields


def confidence_for_match(match: dict[str, Any]) -> str:
    if match.get("match_type") in {"exact_title", "exact_normalized_title"} and match.get("similarity_score") == 1.0:
        return "high"
    if float(match.get("similarity_score") or 0) >= 0.82:
        return "medium"
    return "low"


def build_upgrade_action(item: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    match = item["duplicate_matches"][0]
    return {
        "candidate_index": item["candidate_index"],
        "candidate_title": item["candidate_title"],
        "existing_recipe_id": match["db_id"],
        "existing_title": match["db_title"],
        "confidence": confidence_for_match(match),
        "reason": item["reason"],
        "proposed_action": "upgrade_existing_recipe",
        "fields_to_replace": fields_to_replace(candidate, match),
        "fields_to_preserve": fields_to_preserve(match),
        "preserve_existing_images": bool(match.get("db_has_images")),
        "add_tags": ["gold_v3", "recipe_schema_v3", "upgraded_from_legacy"],
        "no_new_recipe_id": True,
    }


def build_manual_review_card(item: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_index": item["candidate_index"],
        "candidate_title": item["candidate_title"],
        "candidate_ingredients_summary": item.get("candidate_main_ingredients") or duplicates.main_ingredients(candidate),
        "candidate_meal_type": item.get("candidate_meal_type"),
        "candidate_category": item.get("candidate_category"),
        "candidate_tags": item.get("candidate_tags") or [],
        "matched_db_recipes": [
            {
                "id": match["db_id"],
                "title": match["db_title"],
                "source_type": match.get("db_source_type"),
                "meal_type": match.get("db_meal_type"),
                "category": match.get("db_category"),
                "ingredient_overlap": match["similarity_score"] if match["match_type"] == "ingredient_overlap" else None,
                "title_similarity": match["similarity_score"] if match["match_type"] != "ingredient_overlap" else None,
                "match_type": match["match_type"],
            }
            for match in item.get("duplicate_matches", [])
        ],
        "manual_review_reason": item["reason"],
        "proposed_decision": "keep_manual_review",
        "human_decision_needed": (
            "Decide whether this candidate is the same dish to upgrade, a distinct recipe to rename later, "
            "or a duplicate to skip."
        ),
    }


def build_do_not_upgrade(item: dict[str, Any]) -> dict[str, Any]:
    match = item["duplicate_matches"][0] if item.get("duplicate_matches") else {}
    return {
        "candidate_index": item["candidate_index"],
        "candidate_title": item["candidate_title"],
        "existing_recipe_id": match.get("db_id"),
        "existing_title": match.get("db_title"),
        "proposed_action": "do_not_upgrade",
        "reason": item["reason"],
    }


def relation_safety(
    planned_recipe_ids: list[int],
    *,
    database_url: str | None = None,
    relation_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if relation_snapshot is not None:
        return relation_snapshot
    if not planned_recipe_ids:
        return {
            "relation_check_available": True,
            "planned_recipe_ids": [],
            "tables_checked": [],
            "references_by_recipe_id": {},
            "future_apply_requires_pre_apply_backup": True,
        }
    database_url = database_url or os.getenv("DATABASE_URL") or "postgresql://aifood:aifood@localhost:5432/aifood"
    try:
        from sqlalchemy import create_engine, inspect, text
    except Exception as exc:  # pragma: no cover - depends on local env
        return {
            "relation_check_available": False,
            "reason": f"sqlalchemy_unavailable:{exc}",
            "planned_recipe_ids": planned_recipe_ids,
            "future_apply_requires_pre_apply_backup": True,
        }
    try:
        engine = create_engine(database_url, future=True)
        references: dict[str, dict[str, int]] = defaultdict(dict)
        tables_checked = []
        with engine.connect() as conn:
            inspector = inspect(conn)
            for table_name in inspector.get_table_names():
                columns = {column["name"] for column in inspector.get_columns(table_name)}
                if "recipe_id" not in columns:
                    continue
                if table_name in {"recipe_ingredients", "recipe_steps"} or any(hint in table_name for hint in RELATION_TABLE_HINTS):
                    tables_checked.append(table_name)
                    for recipe_id in planned_recipe_ids:
                        count = conn.execute(
                            text(f"select count(*) from {table_name} where recipe_id = :recipe_id"),
                            {"recipe_id": recipe_id},
                        ).scalar_one()
                        if count:
                            references[str(recipe_id)][table_name] = int(count)
        return {
            "relation_check_available": True,
            "planned_recipe_ids": planned_recipe_ids,
            "tables_checked": sorted(tables_checked),
            "references_by_recipe_id": dict(references),
            "appears_in_menu_or_plans": relation_hit(references, ("meal", "plan", "menu")),
            "appears_in_cooked_or_history": relation_hit(references, ("cooked", "history")),
            "appears_in_favorites": relation_hit(references, ("favorite",)),
            "shopping_lists_may_be_affected": relation_hit(references, ("shopping",)),
            "future_apply_requires_pre_apply_backup": True,
        }
    except Exception as exc:
        return {
            "relation_check_available": False,
            "reason": str(exc),
            "planned_recipe_ids": planned_recipe_ids,
            "future_apply_requires_pre_apply_backup": True,
        }


def relation_hit(references: dict[str, dict[str, int]], hints: tuple[str, ...]) -> bool:
    return any(any(hint in table for hint in hints) for table_counts in references.values() for table in table_counts)


def future_apply_design() -> dict[str, Any]:
    return {
        "report_only": True,
        "executable_apply_implemented": False,
        "steps": [
            "Backup DB first.",
            "Update existing recipes by preserving IDs.",
            "Replace recipe_ingredients and recipe_steps transactionally.",
            "Preserve image URLs unless candidate has approved generated images.",
            "Add gold_v3, recipe_schema_v3, upgraded_from_legacy tags.",
            "Never delete user history.",
            "Never break menu references.",
            "Provide rollback script/report.",
        ],
    }


def build_plan(
    duplicate_report: dict[str, Any] | None = None,
    candidates: list[dict[str, Any]] | None = None,
    *,
    relation_snapshot: dict[str, Any] | None = None,
    write_reports: bool = True,
    write_plan: bool = False,
) -> dict[str, Any]:
    candidates_by_index = load_candidates_by_index(candidates)
    duplicate_report = duplicate_report or load_duplicate_report(candidates)
    upgrade_actions = []
    manual_review_cards = []
    do_not_upgrade = []
    import_new_recipe = []
    all_items = []
    for item in duplicate_report.get("items") or []:
        candidate = candidates_by_index.get(int(item["candidate_index"]), {})
        decision = item.get("decision")
        if decision == "candidate_for_future_upgrade" and item.get("duplicate_matches"):
            action = build_upgrade_action(item, candidate)
            upgrade_actions.append(action)
            plan_decision = "upgrade_existing_recipe"
        elif decision == "manual_review":
            action = build_manual_review_card(item, candidate)
            manual_review_cards.append(action)
            plan_decision = "manual_review"
        elif decision == "skip_exact_duplicate":
            action = build_do_not_upgrade(item)
            do_not_upgrade.append(action)
            plan_decision = "do_not_upgrade"
        else:
            action = {
                "candidate_index": item["candidate_index"],
                "candidate_title": item["candidate_title"],
                "proposed_action": "import_new_recipe_blocked_in_this_sprint",
                "reason": "New recipe import is out of scope for Sprint 1.3E-UPGRADE-PLAN.",
            }
            import_new_recipe.append(action)
            plan_decision = "import_new_recipe"
        all_items.append({"candidate_index": item["candidate_index"], "candidate_title": item["candidate_title"], "plan_decision": plan_decision})

    planned_ids = sorted({int(action["existing_recipe_id"]) for action in upgrade_actions if action.get("existing_recipe_id")})
    relation = relation_safety(planned_ids, relation_snapshot=relation_snapshot)
    action_counts = {
        "upgrade_existing_recipe": len(upgrade_actions),
        "manual_review": len(manual_review_cards),
        "do_not_upgrade": len(do_not_upgrade),
        "import_new_recipe": len(import_new_recipe),
    }
    future_apply_blocked = (
        not duplicate_report.get("db_available")
        or action_counts["manual_review"] > 0
        or action_counts["import_new_recipe"] > 0
    )
    report = {
        "generated_at": now(),
        "input": str(INPUT.relative_to(ROOT)),
        "duplicate_report_input": str(DUPLICATE_REPORT_JSON.relative_to(ROOT)),
        "read_only": True,
        "db_writes": 0,
        "total_candidates": len(duplicate_report.get("items") or []),
        "duplicate_risk_count": duplicate_report.get("duplicate_risk_count"),
        "action_counts": action_counts,
        "planned_existing_recipe_ids": planned_ids,
        "upgrade_actions": upgrade_actions,
        "manual_review_cards": manual_review_cards,
        "do_not_upgrade": do_not_upgrade,
        "import_new_recipe": import_new_recipe,
        "all_candidates": all_items,
        "relation_safety": relation,
        "future_apply_blocked": future_apply_blocked,
        "future_apply_blockers": future_apply_blockers(duplicate_report, action_counts, relation),
        "future_apply_design": future_apply_design(),
        "recommendation": recommendation(action_counts, future_apply_blocked),
    }
    if write_reports:
        REPORTS.mkdir(exist_ok=True)
        REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        REPORT_MD.write_text(render(report), encoding="utf-8")
        if write_plan:
            write_commit_safe_plan(report)
    return report


def future_apply_blockers(
    duplicate_report: dict[str, Any],
    action_counts: dict[str, int],
    relation: dict[str, Any],
) -> list[str]:
    blockers = []
    if not duplicate_report.get("db_available"):
        blockers.append("db_duplicate_report_unavailable")
    if action_counts["manual_review"]:
        blockers.append("manual_review_remaining")
    if action_counts["import_new_recipe"]:
        blockers.append("new_recipe_import_out_of_scope")
    if not relation.get("relation_check_available"):
        blockers.append("relation_check_unavailable")
    return blockers


def recommendation(action_counts: dict[str, int], future_apply_blocked: bool) -> str:
    if action_counts["manual_review"]:
        return "classify_manual_review_7_before_apply"
    if future_apply_blocked:
        return "do_not_apply"
    return "prepare_controlled_upgrade_apply_sprint"


def write_commit_safe_plan(report: dict[str, Any]) -> None:
    plan = {
        "source": "gold_recipes_30_repaired_candidate.jsonl",
        "total_candidates": report["total_candidates"],
        "planned_existing_recipe_ids": report["planned_existing_recipe_ids"],
        "upgrade_actions": [
            {
                "candidate_index": action["candidate_index"],
                "candidate_title": action["candidate_title"],
                "existing_recipe_id": action["existing_recipe_id"],
                "existing_title": action["existing_title"],
                "confidence": action["confidence"],
                "proposed_action": action["proposed_action"],
                "fields_to_replace": action["fields_to_replace"],
                "fields_to_preserve": action["fields_to_preserve"],
            }
            for action in report["upgrade_actions"]
        ],
        "manual_review_candidates": [
            {
                "candidate_index": card["candidate_index"],
                "candidate_title": card["candidate_title"],
                "matched_db_ids": [match["id"] for match in card["matched_db_recipes"]],
                "proposed_decision": card["proposed_decision"],
            }
            for card in report["manual_review_cards"]
        ],
        "future_apply_blocked": report["future_apply_blocked"],
    }
    if has_source_leakage(plan):
        raise RuntimeError("upgrade plan contains source leakage")
    PLAN_JSON.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def render(report: dict[str, Any]) -> str:
    lines = [
        "# Sprint 1.3E Gold V3 Existing Recipe Upgrade Plan",
        "",
        f"Generated: `{report['generated_at']}`",
        f"Read-only: `{report['read_only']}`",
        f"DB writes: `{report['db_writes']}`",
        f"total_candidates: `{report['total_candidates']}`",
        f"duplicate_risk_count: `{report['duplicate_risk_count']}`",
        f"future_apply_blocked: `{report['future_apply_blocked']}`",
        f"future_apply_blockers: `{report['future_apply_blockers']}`",
        f"recommendation: `{report['recommendation']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["action_counts"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            f"- planned_existing_recipe_ids: `{report['planned_existing_recipe_ids']}`",
            "",
            "## Upgrade Existing Recipes",
            "",
        ]
    )
    if report["upgrade_actions"]:
        for action in report["upgrade_actions"]:
            lines.append(
                f"- candidate {action['candidate_index']} `{action['candidate_title']}` -> "
                f"recipe `{action['existing_recipe_id']}` `{action['existing_title']}`, "
                f"confidence=`{action['confidence']}`"
            )
            lines.append(f"  replace=`{action['fields_to_replace']}`")
            lines.append(f"  preserve=`{action['fields_to_preserve']}`")
    else:
        lines.append("- none")
    lines.extend(["", "## Manual Review", ""])
    if report["manual_review_cards"]:
        for card in report["manual_review_cards"]:
            matches = ", ".join(
                f"{match['id']}:{match['title']}:{match['match_type']}" for match in card["matched_db_recipes"]
            )
            lines.append(
                f"- candidate {card['candidate_index']} `{card['candidate_title']}`: "
                f"matches=`{matches}`, proposed_decision=`{card['proposed_decision']}`"
            )
            lines.append(f"  need=`{card['human_decision_needed']}`")
    else:
        lines.append("- none")
    relation = report["relation_safety"]
    lines.extend(
        [
            "",
            "## Relation Safety",
            "",
            f"relation_check_available: `{relation.get('relation_check_available')}`",
            f"tables_checked: `{relation.get('tables_checked')}`",
            f"references_by_recipe_id: `{relation.get('references_by_recipe_id')}`",
            f"future_apply_requires_pre_apply_backup: `{relation.get('future_apply_requires_pre_apply_backup')}`",
            "",
            "## Future Controlled Apply Design",
            "",
            f"report_only: `{report['future_apply_design']['report_only']}`",
            f"executable_apply_implemented: `{report['future_apply_design']['executable_apply_implemented']}`",
        ]
    )
    lines.extend(f"- {step}" for step in report["future_apply_design"]["steps"])
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-plan", action="store_true", help="Write commit-safe data plan JSON.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = build_plan(write_plan=args.write_plan)
    print(f"Wrote {REPORT_MD}")
    return 0 if report["total_candidates"] == 30 else 1


if __name__ == "__main__":
    raise SystemExit(main())
