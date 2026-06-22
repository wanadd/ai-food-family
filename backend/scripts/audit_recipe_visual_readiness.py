"""Read-only recipe visual readiness audit for Gold V3 and catalog."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "backend" / "scripts"
API_ROOT = ROOT / "apps" / "api"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
if (API_ROOT / "app").is_dir() and str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))
elif (ROOT / "app").is_dir() and str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from audit_gold_v3_post_apply_common import (  # noqa: E402
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

REPORT_JSON = ROOT / "reports" / "SPRINT_1_4_RECIPE_VISUAL_READINESS.json"
REPORT_MD = ROOT / "reports" / "SPRINT_1_4_RECIPE_VISUAL_READINESS.md"
PHOTO_PLAN_MD = ROOT / "reports" / "SPRINT_1_4_PHOTO_READINESS_PLAN.md"
PILOT_IDS = list(range(256, 266))
REQUIRED_IMAGE_FILES = {
    "hero": ("hero_image_url", "hero.webp"),
    "card": ("image_url", "card_800.webp"),
    "thumb": ("thumbnail_url", "thumb_400.webp"),
}
PUBLIC_BASE_DEFAULT = os.environ.get("PLANAM_PUBLIC_BASE_URL", "https://planam.ru")


def looks_like_raw_json(value: Any) -> bool:
    if isinstance(value, (list, dict)):
        return False
    if not isinstance(value, str):
        return False
    text = value.strip()
    return text.startswith("[") or text.startswith("{")


def image_fields(recipe_row: dict[str, Any]) -> dict[str, Any]:
    hero = recipe_row.get("hero_image_url")
    card = recipe_row.get("image_url")
    thumb = recipe_row.get("thumbnail_url")
    values = {"hero_image_url": hero, "image_url": card, "thumbnail_url": thumb}
    safe = {key: image_field_safe(value) for key, value in values.items()}
    present = {key: bool(str(value or "").strip()) for key, value in values.items()}
    broken = []
    for key, value in values.items():
        if value is None or value == "":
            continue
        text = str(value).strip().lower()
        if text in {"null", "undefined", "nan", "none"} or not safe[key]:
            broken.append(key)
    all_present = all(present.values())
    any_present = any(present.values())
    return {
        "hero_present": present["hero_image_url"],
        "card_present": present["image_url"],
        "thumb_present": present["thumbnail_url"],
        "all_three_present": all_present,
        "any_present": any_present,
        "broken_fields": broken,
        "safe_placeholder_ok": not any_present and not broken,
        "urls": values,
    }


def check_public_url(base_url: str, recipe_id: int, filename: str, timeout: int = 10) -> bool:
    url = f"{base_url.rstrip('/')}/recipe-images/{recipe_id}/{filename}"
    request = Request(url, method="HEAD")
    try:
        with urlopen(request, timeout=timeout) as response:
            return 200 <= response.status < 400
    except HTTPError as exc:
        return 200 <= exc.code < 400
    except (URLError, TimeoutError, OSError):
        return False


def load_user_facing_payloads(recipe_ids: list[int], database_url: str | None = None) -> dict[int, dict[str, Any]]:
    from sqlalchemy.orm import Session, joinedload

    from app.models.recipe import Recipe
    from app.services.recipes.mapper import to_detail

    create_engine, _ = import_sqlalchemy()
    engine = create_engine(database_url or os.environ.get("DATABASE_URL"), pool_pre_ping=True)
    payloads: dict[int, dict[str, Any]] = {}
    with engine.connect() as conn:
        session = Session(bind=conn)
        rows = (
            session.query(Recipe)
            .options(
                joinedload(Recipe.ingredient_rows),
                joinedload(Recipe.step_rows),
                joinedload(Recipe.tag_rows),
            )
            .filter(Recipe.id.in_(recipe_ids))
            .all()
        )
        for recipe in rows:
            detail = to_detail(recipe, set())
            payloads[int(recipe.id)] = detail.model_dump(mode="json")
        session.close()
    return payloads


def fetch_active_recipe_rows(database_url: str | None = None) -> list[dict[str, Any]]:
    create_engine, text = import_sqlalchemy()
    assert text is not None
    engine = create_engine(database_url or os.environ.get("DATABASE_URL"), pool_pre_ping=True)
    with engine.connect() as conn:
        return [
            dict(row._mapping)
            for row in conn.execute(
                text(
                    """
                    SELECT id, title, display_title, description, meal_type,
                           hero_image_url, image_url, thumbnail_url, is_active
                    FROM recipes
                    WHERE is_active = TRUE
                    ORDER BY id
                    """
                )
            )
        ]


def evaluate_recipe(
    row: dict[str, Any],
    payload: dict[str, Any] | None,
    *,
    cohort: str,
    check_public: bool = False,
    public_base: str = PUBLIC_BASE_DEFAULT,
) -> dict[str, Any]:
    recipe_id = int(row["id"])
    images = image_fields(row)
    blockers: list[str] = []
    warnings: list[str] = []

    title = str(payload.get("title") if payload else row.get("display_title") or row.get("title") or "").strip()
    if not title:
        blockers.append("title_empty")
    blockers.extend(f"title_garbage:{item}" for item in title_garbage(title))
    try:
        from app.services.recipes.title_display import title_cleanliness_blockers

        blockers.extend(title_cleanliness_blockers(title))
    except Exception:
        pass

    description = str((payload or {}).get("description") or row.get("description") or "").strip()
    if not description:
        blockers.append("description_empty_user_facing")

    if payload:
        ingredients = payload.get("ingredients") or []
        steps = payload.get("steps") or []
        if not ingredients:
            blockers.append("ingredients_empty")
        if not steps:
            blockers.append("steps_empty")
        for ing in ingredients:
            amount = str(ing.get("amount") or "")
            if looks_like_raw_json(amount) or has_user_facing_garbage(amount):
                blockers.append("raw_json_render_risk:ingredient_amount")
        for step in steps:
            if looks_like_raw_json(step):
                blockers.append("raw_json_render_risk:step")
        user_fields = [
            title,
            description,
            *[str(ing.get("name") or "") for ing in ingredients],
            *[str(ing.get("amount") or "") for ing in ingredients],
            *[str(step) for step in steps],
        ]
        if has_source_leakage(" ".join(user_fields).lower()):
            blockers.append("source_leakage")
        if any(has_user_facing_garbage(field) for field in user_fields if field):
            blockers.append("user_facing_garbage")
        nutrition_values = [
            payload.get("calories_per_serving"),
            payload.get("protein_g"),
            payload.get("fat_g"),
            payload.get("carbs_g"),
        ]
        if not any(v is not None for v in nutrition_values):
            warnings.append("nutrition_missing")
    elif not description:
        warnings.append("payload_unavailable")

    if images["broken_fields"]:
        blockers.append(f"broken_image_refs:{','.join(images['broken_fields'])}")
    if not images["any_present"]:
        warnings.append("missing_images")
    if cohort == "pilot" and not images["all_three_present"]:
        blockers.append("pilot_images_incomplete")
    if check_public and cohort == "pilot":
        for _, filename in REQUIRED_IMAGE_FILES.values():
            if not check_public_url(public_base, recipe_id, filename):
                blockers.append(f"public_url_missing:{filename}")

    return {
        "id": recipe_id,
        "cohort": cohort,
        "title": title,
        "images": images,
        "blockers": sorted(set(blockers)),
        "warnings": warnings,
        "ok": not blockers,
    }


def summarize(items: list[dict[str, Any]]) -> dict[str, Any]:
    with_images = sum(1 for item in items if item["images"]["any_present"])
    missing_images = sum(1 for item in items if "missing_images" in item["warnings"])
    broken = sum(1 for item in items if any(b.startswith("broken_image_refs") for b in item["blockers"]))
    placeholder_ok = sum(1 for item in items if item["images"]["safe_placeholder_ok"])
    hard_fail = sum(1 for item in items if item["blockers"])
    return {
        "recipes_checked": len(items),
        "with_images": with_images,
        "missing_images": missing_images,
        "broken_image_refs": broken,
        "safe_placeholder_ok": placeholder_ok,
        "hard_fail": hard_fail,
        "passed": hard_fail == 0,
    }


def build_photo_plan(report: dict[str, Any]) -> str:
    upgraded = report["cohorts"]["upgraded"]
    pilot = report["cohorts"]["pilot"]
    catalog = report["cohorts"]["catalog_summary"]
    priority_missing = [
        item["id"]
        for item in report["items"]
        if item["cohort"] == "upgraded" and "missing_images" in item["warnings"]
    ]
    lines = [
        "# Sprint 1.4 Photo Readiness Plan",
        "",
        f"Generated: `{report['generated_at']}`",
        "",
        "## Current state",
        "",
        f"- upgraded recipes checked: `{upgraded['recipes_checked']}`",
        f"- upgraded with images: `{upgraded['with_images']}`",
        f"- upgraded missing images: `{upgraded['missing_images']}`",
        f"- pilot recipes checked: `{pilot['recipes_checked']}`",
        f"- pilot with all 3 URLs: `{pilot['with_images']}`",
        f"- active catalog total: `{catalog['recipes_checked']}`",
        f"- catalog with any image URL: `{catalog['with_images']}`",
        f"- catalog missing images: `{catalog['missing_images']}`",
        "",
        "## Priority IDs for future photo sprint",
        "",
        "### Pilot (already have assets)",
        "",
        ", ".join(str(recipe_id) for recipe_id in PILOT_IDS),
        "",
        "### Upgraded Gold V3 missing images (priority)",
        "",
        ", ".join(str(recipe_id) for recipe_id in priority_missing[:30]) or "(none)",
        "",
        "## Required sizes / files",
        "",
        "| variant | file | typical use |",
        "| --- | --- | --- |",
        "| hero | `hero.webp` | recipe detail header (~1200w) |",
        "| card | `card_800.webp` | catalog grid (~800w) |",
        "| thumb | `thumb_400.webp` | menu thumb (~400w) |",
        "",
        "## Storage layout",
        "",
        "- Host path (prod): `/var/www/ai-food-family-data/recipe-images/{id}/`",
        "- Container mount: `/app/public/recipe-images/{id}/`",
        "- Public URL: `https://planam.ru/recipe-images/{id}/hero.webp` (and card/thumb)",
        "- DB fields: `hero_image_url`, `image_url`, `thumbnail_url` as `/recipe-images/{id}/...`",
        "- Do not commit generated binaries to git; use external persistent volume",
        "",
        "## Public URL verification (future sprint)",
        "",
        "```bash",
        "python backend/scripts/verify_gold_v3_pilot_10_assets.py --public-base-url https://planam.ru",
        "python backend/scripts/audit_recipe_visual_readiness.py",
        "```",
        "",
        "## Explicit guard",
        "",
        "- Photo generation: **NOT RUN** in Sprint 1.4",
        "- Recipe generation: **NOT RUN**",
        "- DB mutation: **NOT RUN**",
        "",
        "## Frontend placeholder",
        "",
        "- UI uses `RecipeImage2026` + `MealFallbackPlate2026` when no image URL",
        "- Missing images are acceptable for upgraded cohort if placeholder renders; pilot must have real assets",
        "",
    ]
    return "\n".join(lines) + "\n"


def build_report() -> dict[str, Any]:
    database_url = os.environ.get("DATABASE_URL")
    public_base = os.environ.get("PLANAM_PUBLIC_BASE_URL", PUBLIC_BASE_DEFAULT)
    if import_sqlalchemy() is None:
        return {"generated_at": now(), "ok": False, "error": "sqlalchemy_unavailable", "items": []}

    upgraded_ids = extract_upgraded_recipe_ids().get("recipe_ids") or []
    all_ids = sorted(set(upgraded_ids) | set(PILOT_IDS))
    try:
        active_rows = fetch_active_recipe_rows(database_url)
        payloads = load_user_facing_payloads(all_ids, database_url)
    except Exception as exc:
        return {
            "generated_at": now(),
            "ok": False,
            "error": repr(exc),
            "database_url": redact_url(database_url or ""),
            "items": [],
        }

    row_by_id = {int(row["id"]): row for row in active_rows}
    items: list[dict[str, Any]] = []

    for recipe_id in upgraded_ids:
        row = row_by_id.get(recipe_id)
        if not row:
            items.append(
                {
                    "id": recipe_id,
                    "cohort": "upgraded",
                    "title": "",
                    "images": image_fields({}),
                    "blockers": ["recipe_missing"],
                    "warnings": [],
                    "ok": False,
                }
            )
            continue
        items.append(
            evaluate_recipe(
                row,
                payloads.get(recipe_id),
                cohort="upgraded",
                check_public=False,
                public_base=public_base,
            )
        )

    for recipe_id in PILOT_IDS:
        row = row_by_id.get(recipe_id)
        if not row:
            continue
        items.append(
            evaluate_recipe(
                row,
                payloads.get(recipe_id),
                cohort="pilot",
                check_public=bool(os.environ.get("PLANAM_CHECK_PUBLIC_IMAGE_URLS")),
                public_base=public_base,
            )
        )

    catalog_items = []
    for row in active_rows:
        recipe_id = int(row["id"])
        if recipe_id in upgraded_ids or recipe_id in PILOT_IDS:
            continue
        catalog_items.append(
            evaluate_recipe(row, payloads.get(recipe_id), cohort="catalog")
        )

    upgraded_items = [item for item in items if item["cohort"] == "upgraded"]
    pilot_items = [item for item in items if item["cohort"] == "pilot"]
    hard_fail = sum(1 for item in items if item["blockers"])

    report = {
        "generated_at": now(),
        "ok": hard_fail == 0,
        "database_url": redact_url(database_url or ""),
        "public_base_url": public_base,
        "cohorts": {
            "upgraded": summarize(upgraded_items),
            "pilot": summarize(pilot_items),
            "catalog_summary": summarize(catalog_items),
        },
        "items": items,
        "catalog_sample_blockers": [
            item for item in catalog_items if item["blockers"]
        ][:10],
        "top_blockers": sorted({b for item in items for b in item["blockers"]}),
        "photo_generation_run": False,
        "recipe_generation_run": False,
    }
    return report


def render(report: dict[str, Any]) -> str:
    u = report["cohorts"]["upgraded"]
    p = report["cohorts"]["pilot"]
    c = report["cohorts"]["catalog_summary"]
    lines = [
        "# Sprint 1.4 Recipe Visual Readiness",
        "",
        f"Generated: `{report['generated_at']}`",
        f"ok: `{report.get('ok')}`",
        "",
        "## Upgraded (2, 227–255)",
        "",
        f"checked: `{u['recipes_checked']}` | with_images: `{u['with_images']}` | missing_images: `{u['missing_images']}` | hard_fail: `{u['hard_fail']}`",
        "",
        "## Pilot (256–265)",
        "",
        f"checked: `{p['recipes_checked']}` | with_images: `{p['with_images']}` | hard_fail: `{p['hard_fail']}`",
        "",
        "## Catalog summary (other active)",
        "",
        f"checked: `{c['recipes_checked']}` | with_images: `{c['with_images']}` | missing_images: `{c['missing_images']}`",
        "",
    ]
    blocked = [item for item in report.get("items") or [] if item.get("blockers")]
    if blocked:
        lines.extend(["## Blocked items", ""])
        for item in blocked[:25]:
            lines.append(f"- [{item['cohort']}] {item['id']} {item['title']}: {item['blockers']}")
    return "\n".join(lines) + "\n"


def main() -> int:
    report = build_report()
    write_json(REPORT_JSON, report)
    if "cohorts" not in report:
        REPORT_MD.write_text(
            f"# Sprint 1.4 Recipe Visual Readiness\n\nerror: `{report.get('error')}`\n",
            encoding="utf-8",
        )
        print(f"Wrote {REPORT_MD} (error)")
        return 1
    REPORT_MD.write_text(render(report), encoding="utf-8")
    PHOTO_PLAN_MD.write_text(build_photo_plan(report), encoding="utf-8")
    print(f"Wrote {REPORT_MD}")
    print(f"Wrote {PHOTO_PLAN_MD}")
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
