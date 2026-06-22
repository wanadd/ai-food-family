"""Read-only product polish audit for upgraded Gold V3 recipes."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "backend" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from audit_gold_v3_post_apply_common import (  # noqa: E402
    ENGLISH_TITLE_PREFIX_RE,
    SOURCE_LEAKAGE_MARKERS,
    USER_FACING_GARBAGE,
    extract_upgraded_recipe_ids,
    has_source_leakage,
    has_user_facing_garbage,
    image_field_safe,
    import_sqlalchemy,
    now,
    redact_url,
    title_garbage,
    write_json,
)

REPORT_JSON = ROOT / "reports" / "SPRINT_1_3N_PRODUCT_POLISH_AUDIT.json"
REPORT_MD = ROOT / "reports" / "SPRINT_1_3N_PRODUCT_POLISH_AUDIT.md"
TECHNICAL_TAGS = {
    "gold_v3",
    "recipe_schema_v3",
    "upgraded_from_legacy",
    "status:gold",
    "recipe_schema_v2",
    "gold_v2",
}


def load_recipes(recipe_ids: list[int], database_url: str | None = None) -> list[Any]:
    from sqlalchemy.orm import joinedload

    from app.models.recipe import Recipe
    from app.services.recipes.mapper import to_detail
    from app.services.recipes.description_display import public_description

    create_engine, _ = import_sqlalchemy()
    engine = create_engine(database_url or os.environ.get("DATABASE_URL"), pool_pre_ping=True)
    with engine.connect() as conn:
        from sqlalchemy.orm import Session

        session = Session(bind=conn)
        rows = (
            session.query(Recipe)
            .options(
                joinedload(Recipe.ingredient_rows),
                joinedload(Recipe.step_rows),
                joinedload(Recipe.tag_rows),
            )
            .filter(Recipe.id.in_(recipe_ids))
            .order_by(Recipe.id)
            .all()
        )
        payloads = []
        for recipe in rows:
            detail = to_detail(recipe, set())
            payload = detail.model_dump(mode="json")
            payload["description_display"] = public_description(recipe)
            payload["description_db_empty"] = not (recipe.description or "").strip()
            payloads.append((recipe, payload))
        session.close()
    return payloads


def looks_like_raw_json(value: Any) -> bool:
    if isinstance(value, (list, dict)):
        return False
    if not isinstance(value, str):
        return False
    text = value.strip()
    return text.startswith("[") or text.startswith("{")


def evaluate_payload(recipe_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []

    description_display = str(payload.get("description_display") or "").strip()
    if not description_display:
        blockers.append("description_empty_user_facing")

    title = str(payload.get("title") or "").strip()
    if not title:
        blockers.append("title_empty")
    blockers.extend(f"title_garbage:{item}" for item in title_garbage(title))

    ingredients = payload.get("ingredients") or []
    steps = payload.get("steps") or []
    if not ingredients:
        blockers.append("ingredients_empty")
    if not steps:
        blockers.append("steps_empty")
    for ing in ingredients:
        if not str(ing.get("name") or "").strip():
            blockers.append("ingredient_name_empty")
        amount = str(ing.get("amount") or "")
        if looks_like_raw_json(amount) or has_user_facing_garbage(amount):
            blockers.append("raw_json_render_risk:ingredient_amount")
    if looks_like_raw_json(ingredients):
        blockers.append("raw_json_render_risk:ingredients")
    if looks_like_raw_json(steps):
        blockers.append("raw_json_render_risk:steps")
    for step in steps:
        if looks_like_raw_json(step):
            blockers.append("raw_json_render_risk:step")

    nutrition_blob = json.dumps(
        {
            "calories_per_serving": payload.get("calories_per_serving"),
            "protein_g": payload.get("protein_g"),
            "fat_g": payload.get("fat_g"),
            "carbs_g": payload.get("carbs_g"),
            "nutrition_summary": payload.get("nutrition_summary"),
        },
        ensure_ascii=False,
    )
    if has_user_facing_garbage(nutrition_blob):
        blockers.append("nutrition_garbage")

    for field in ("hero_image_url", "image_url", "thumbnail_url"):
        if not image_field_safe(payload.get(field)):
            blockers.append(f"image_unsafe:{field}")

    user_blob = json.dumps(payload, ensure_ascii=False).lower()
    leakage = has_source_leakage(user_blob)
    if leakage:
        blockers.append(f"source_leakage:{','.join(leakage)}")
    if ENGLISH_TITLE_PREFIX_RE.search(title):
        blockers.append("english_title_prefix")

    rendered_tags = {str(tag).lower() for tag in (payload.get("tags") or [])}
    leaked_technical_tags = sorted(tag for tag in rendered_tags if tag in TECHNICAL_TAGS)
    if leaked_technical_tags and any(tag in user_blob for tag in leaked_technical_tags):
        warnings.append(f"technical_tags_in_payload:{leaked_technical_tags}")

    if payload.get("description_db_empty"):
        warnings.append("description_db_empty_fallback_used")

    return {
        "id": recipe_id,
        "title": title,
        "description_display": description_display,
        "blockers": sorted(set(blockers)),
        "warnings": warnings,
        "ok": not blockers,
    }


def build_report() -> dict[str, Any]:
    database_url = os.environ.get("DATABASE_URL")
    id_report = extract_upgraded_recipe_ids()
    recipe_ids = id_report.get("recipe_ids") or []
    if import_sqlalchemy() is None:
        return {
            "generated_at": now(),
            "ok": False,
            "hard_fail": 1,
            "error": "sqlalchemy_unavailable",
            "items": [],
        }
    try:
        loaded = load_recipes(recipe_ids, database_url)
    except Exception as exc:
        return {
            "generated_at": now(),
            "ok": False,
            "hard_fail": 1,
            "error": repr(exc),
            "database_url": redact_url(database_url or ""),
            "items": [],
        }

    items = [evaluate_payload(int(payload["id"]), payload) for _, payload in loaded]
    hard_fail = sum(1 for item in items if item["blockers"])
    description_empty_user_facing = sum(
        1 for item in items if "description_empty_user_facing" in item["blockers"]
    )
    raw_json_render_risk = sum(
        1 for item in items if any(b.startswith("raw_json_render_risk") for b in item["blockers"])
    )
    source_leakage = sum(
        1 for item in items if any(b.startswith("source_leakage") for b in item["blockers"])
    )

    return {
        "generated_at": now(),
        "ok": hard_fail == 0,
        "hard_fail": hard_fail,
        "description_empty_user_facing": description_empty_user_facing,
        "raw_json_render_risk": raw_json_render_risk,
        "source_leakage": source_leakage,
        "recipe_id_count": len(recipe_ids),
        "database_url": redact_url(database_url or ""),
        "prod_http_smoke_decision": "prod_http_smoke_skipped_by_design: auth_required",
        "items": items,
        "top_blockers": sorted({blocker for item in items for blocker in item["blockers"]}),
    }


def render(report: dict[str, Any]) -> str:
    lines = [
        "# Sprint 1.3N Gold V3 Product Polish Audit",
        "",
        f"Generated: `{report['generated_at']}`",
        f"ok: `{report.get('ok')}`",
        f"hard_fail: `{report.get('hard_fail')}`",
        f"description_empty_user_facing: `{report.get('description_empty_user_facing')}`",
        f"raw_json_render_risk: `{report.get('raw_json_render_risk')}`",
        f"source_leakage: `{report.get('source_leakage')}`",
        f"prod_http_smoke: `{report.get('prod_http_smoke_decision')}`",
        "",
    ]
    blocked = [item for item in report.get("items") or [] if item.get("blockers")]
    if blocked:
        lines.extend(["## Blocked", ""])
        for item in blocked[:20]:
            lines.append(f"- {item['id']} {item['title']}: {item['blockers']}")
    return "\n".join(lines) + "\n"


def main() -> int:
    report = build_report()
    write_json(REPORT_JSON, report)
    REPORT_MD.write_text(render(report), encoding="utf-8")
    print(f"Wrote {REPORT_MD}")
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
