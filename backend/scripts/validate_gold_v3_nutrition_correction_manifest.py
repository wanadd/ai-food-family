"""Validate Sprint 1.7 Gold V3 nutrition correction manifest."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "data" / "recipe_v2" / "gold_v3_nutrition_correction_manifest.json"
REPORT_MD = ROOT / "reports" / "SPRINT_1_7_NUTRITION_CORRECTION_MANIFEST_VALIDATION.md"
REPORT_JSON = ROOT / "reports" / "SPRINT_1_7_NUTRITION_CORRECTION_MANIFEST_VALIDATION.json"
EXPECTED_IDS = [2, *range(227, 266)]
ALLOWED_CONFIDENCE = {"reviewed", "estimated", "rough"}
ALLOWED_BASIS = {
    "estimated_cooked_per_serving",
    "reviewed_cooked_per_serving",
    "rough_cooked_per_serving",
}
BAD_TITLE_RE = re.compile(
    r"(халяль|кошер|постный|православ|мусульман|боул|смузи|тост|стир[-\s]*фрай|лёгкий ужин:|семейный ужин:|детский перекус:|для похудения:|для спортсменов:)",
    re.I,
)
LEAKAGE_RE = re.compile(r"(source_url|original_url|povarenok|поваренок|https?://)", re.I)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_manifest(path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def macro_kcal(per: dict[str, Any]) -> float:
    return float(per.get("protein_g") or 0) * 4 + float(per.get("carbs_g") or 0) * 4 + float(per.get("fat_g") or 0) * 9


def validate_manifest(data: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    recipes = data.get("recipes") if isinstance(data.get("recipes"), list) else []
    ids = [int(item.get("recipe_id")) for item in recipes if item.get("recipe_id") is not None]
    duplicate_ids = sorted({rid for rid in ids if ids.count(rid) > 1})
    missing_ids = [rid for rid in EXPECTED_IDS if rid not in ids]
    extra_ids = [rid for rid in ids if rid not in EXPECTED_IDS]

    if len(recipes) != 40:
        blockers.append(f"recipe_count_not_40:{len(recipes)}")
    if missing_ids:
        blockers.append(f"missing_ids:{missing_ids}")
    if extra_ids:
        blockers.append(f"extra_ids:{extra_ids}")
    if duplicate_ids:
        blockers.append(f"duplicate_ids:{duplicate_ids}")

    items: list[dict[str, Any]] = []
    for idx, recipe in enumerate(recipes):
        rid = recipe.get("recipe_id")
        item_blockers: list[str] = []
        item_warnings: list[str] = []
        title = str(recipe.get("display_title") or "")
        text = json.dumps(recipe, ensure_ascii=False)
        if BAD_TITLE_RE.search(title):
            item_blockers.append("bad_title_term")
        if LEAKAGE_RE.search(text):
            item_blockers.append("source_leakage")
        for field in ("servings", "serving_weight_g", "nutrition_basis", "nutrition_confidence", "cooking_method", "yield_notes", "rationale"):
            if recipe.get(field) in (None, "", []):
                item_blockers.append(f"missing_{field}")
        if recipe.get("nutrition_confidence") not in ALLOWED_CONFIDENCE:
            item_blockers.append("invalid_nutrition_confidence")
        if recipe.get("nutrition_basis") not in ALLOWED_BASIS:
            item_blockers.append("invalid_nutrition_basis")
        try:
            servings = float(recipe.get("servings"))
            if servings <= 0:
                item_blockers.append("servings_not_positive")
        except (TypeError, ValueError):
            item_blockers.append("servings_invalid")
            servings = 0
        try:
            if float(recipe.get("serving_weight_g")) <= 0:
                item_blockers.append("serving_weight_not_positive")
        except (TypeError, ValueError):
            item_blockers.append("serving_weight_invalid")

        per = recipe.get("nutrition_per_serving") or {}
        try:
            kcal = float(per.get("kcal"))
            protein = float(per.get("protein_g"))
            fat = float(per.get("fat_g"))
            carbs = float(per.get("carbs_g"))
        except (TypeError, ValueError):
            item_blockers.append("nutrition_per_serving_invalid")
            kcal = protein = fat = carbs = -1
        if kcal <= 0:
            item_blockers.append("kcal_not_positive")
        for key, value in (("protein_g", protein), ("fat_g", fat), ("carbs_g", carbs)):
            if value < 0:
                item_blockers.append(f"{key}_negative")
        expected_kcal = macro_kcal(per) if per else 0
        if kcal > 0 and abs(kcal - expected_kcal) > max(80, kcal * 0.20):
            item_blockers.append("macro_kcal_mismatch")
        if kcal and (kcal < 80 or kcal > 1200):
            item_blockers.append("kcal_out_of_range")
        if protein > 100:
            item_blockers.append("protein_gt_100")
        if fat > 80:
            item_blockers.append("fat_gt_80")
        if carbs > 180:
            item_blockers.append("carbs_gt_180")
        if str(recipe.get("meal_type")) in {"lunch", "dinner"} and kcal < 180:
            item_blockers.append("full_meal_kcal_too_low")
        if str(recipe.get("meal_type")) == "snack" and kcal > 600:
            item_warnings.append("snack_kcal_gt_600")

        blob = f"{title} {recipe.get('cooking_method')} {recipe.get('yield_notes')}".lower()
        if any(term in blob for term in ("рис", "греч", "перлов", "паста", "булгур", "киноа", "овсян")) and "yield" not in str(recipe.get("yield_notes", "")).lower() and "выход" not in str(recipe.get("yield_notes", "")).lower():
            item_blockers.append("dry_grain_without_yield_note")
        if any(term in blob for term in ("суп", "stew", "туш", "рагу")) and not recipe.get("yield_notes"):
            item_blockers.append("soup_stew_without_yield_note")
        if any(term in blob for term in ("oil", "масло", "жар", "frying", "pan")) and fat < 5:
            item_warnings.append("oil_or_frying_fat_low")

        for total_name in ("nutrition_raw_total", "nutrition_cooked_total"):
            total = recipe.get(total_name) or {}
            for key in ("kcal", "protein_g", "fat_g", "carbs_g"):
                if total.get(key) is None:
                    item_blockers.append(f"{total_name}_{key}_missing")

        items.append(
            {
                "recipe_id": rid,
                "title": title,
                "blockers": sorted(set(item_blockers)),
                "warnings": sorted(set(item_warnings)),
                "kcal": kcal,
                "macro_kcal": round(expected_kcal, 1),
            }
        )
        blockers.extend(f"{rid}:{blocker}" for blocker in sorted(set(item_blockers)))
        warnings.extend(f"{rid}:{warning}" for warning in sorted(set(item_warnings)))

    return {
        "generated_at": now(),
        "ok": not blockers,
        "recipe_count": len(recipes),
        "expected_count": 40,
        "ids_count": len(ids),
        "missing_ids": missing_ids,
        "extra_ids": extra_ids,
        "duplicate_ids": duplicate_ids,
        "blockers": blockers,
        "warnings": warnings,
        "items": items,
    }


def render(report: dict[str, Any]) -> str:
    lines = [
        "# Sprint 1.7 Nutrition Correction Manifest Validation",
        "",
        f"Generated: `{report['generated_at']}`",
        f"ok: `{report['ok']}`",
        f"recipe_count: `{report['recipe_count']}`",
        f"missing_ids: `{report['missing_ids']}`",
        f"extra_ids: `{report['extra_ids']}`",
        f"duplicate_ids: `{report['duplicate_ids']}`",
        f"blockers_count: `{len(report['blockers'])}`",
        f"warnings_count: `{len(report['warnings'])}`",
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- `{item}`" for item in report["blockers"][:100])
    if not report["blockers"]:
        lines.append("- none")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- `{item}`" for item in report["warnings"][:100])
    if not report["warnings"]:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def write_reports(report: dict[str, Any]) -> None:
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT_MD.write_text(render(report), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    report = validate_manifest(load_manifest(args.manifest))
    write_reports(report)
    print(f"ok={report['ok']}")
    print(f"recipe_count={report['recipe_count']}")
    print(f"blockers={len(report['blockers'])}")
    print(f"warnings={len(report['warnings'])}")
    print(f"Wrote {REPORT_MD}")
    print(f"Wrote {REPORT_JSON}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
