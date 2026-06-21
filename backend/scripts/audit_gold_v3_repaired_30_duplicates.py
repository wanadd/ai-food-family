"""Read-only duplicate resolution audit for repaired Gold V3 candidates."""

from __future__ import annotations

import json
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "data" / "recipe_v2" / "gold_recipes_30_repaired_candidate.jsonl"
REPORTS = ROOT / "reports"
REPORT_MD = REPORTS / "SPRINT_1_3D_GOLD_V3_DUPLICATE_RESOLUTION.md"
REPORT_JSON = REPORTS / "SPRINT_1_3D_GOLD_V3_DUPLICATE_RESOLUTION.json"
PLAN_JSON = ROOT / "data" / "recipe_v2" / "gold_recipes_30_duplicate_resolution_plan.json"

DECISIONS = {
    "skip_exact_duplicate",
    "candidate_for_future_upgrade",
    "rename_and_import_candidate",
    "safe_to_import",
    "manual_review",
}
MEAT_WORDS = {
    "курица",
    "куриное",
    "куриная",
    "куриной",
    "индейка",
    "индейкой",
    "говядина",
    "говядиной",
    "свинина",
    "рыба",
    "треска",
    "лосось",
    "тунец",
    "креветки",
}
METHOD_WORDS = {
    "запеч",
    "туш",
    "жар",
    "стир",
    "пар",
    "суп",
    "салат",
    "каша",
    "омлет",
    "паста",
}
SOURCE_MARKERS = ("source_url", "original_url", "http", "povarenok", "поваренок")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize(text: Any) -> str:
    value = re.sub(r"[^0-9a-zа-яё]+", " ", str(text or "").lower(), flags=re.I)
    return re.sub(r"\s+", " ", value).strip()


def token_set(text: Any) -> set[str]:
    return set(normalize(text).split())


def similarity(left: Any, right: Any) -> float:
    left_norm = normalize(left)
    right_norm = normalize(right)
    if not left_norm or not right_norm:
        return 0.0
    return round(SequenceMatcher(None, left_norm, right_norm).ratio(), 4)


def title_keywords(title: str, words: set[str]) -> set[str]:
    norm = normalize(title)
    return {word for word in words if word in norm}


def has_source_leakage(value: Any) -> bool:
    text = json.dumps(value, ensure_ascii=False).lower()
    return any(marker in text for marker in SOURCE_MARKERS)


def nutrition_core_complete(recipe: dict[str, Any]) -> bool:
    nutrition = recipe.get("nutrition_per_serving") or {}
    return all(nutrition.get(field) is not None for field in ("kcal", "protein_g", "fat_g", "carbs_g"))


def ingredient_names(recipe: dict[str, Any]) -> list[str]:
    return [
        str(item.get("name") or item.get("display_name") or item.get("canonical_name") or "").strip()
        for item in recipe.get("ingredients") or []
        if str(item.get("name") or item.get("display_name") or item.get("canonical_name") or "").strip()
    ]


def main_ingredients(recipe: dict[str, Any], limit: int = 5) -> list[str]:
    return ingredient_names(recipe)[:limit]


def ingredient_overlap(candidate_names: list[str], db_names: list[str]) -> float:
    candidate = {normalize(name) for name in candidate_names if normalize(name)}
    existing = {normalize(name) for name in db_names if normalize(name)}
    if not candidate or not existing:
        return 0.0
    return round(len(candidate & existing) / max(len(candidate), len(existing)), 4)


def load_candidates(path: Path = INPUT) -> list[dict[str, Any]]:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


@dataclass
class ExistingRecipe:
    id: int
    title: str
    display_title: str | None
    normalized_title: str
    source_type: str | None
    tags: list[str]
    meal_type: str | None
    category: str | None
    has_images: bool
    ingredient_count: int
    step_count: int
    nutrition_core_complete: bool
    ingredient_names: list[str]

    def to_match(self, match_type: str, score: float) -> dict[str, Any]:
        return {
            "db_id": self.id,
            "db_title": self.title,
            "db_display_title": self.display_title,
            "db_normalized_title": self.normalized_title,
            "db_source_type": self.source_type,
            "db_tags": self.tags,
            "db_meal_type": self.meal_type,
            "db_category": self.category,
            "db_has_images": self.has_images,
            "db_ingredient_count": self.ingredient_count,
            "db_step_count": self.step_count,
            "db_nutrition_core_complete": self.nutrition_core_complete,
            "match_type": match_type,
            "similarity_score": score,
        }


def parse_tags(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        except json.JSONDecodeError:
            pass
        return [item.strip() for item in value.split(",") if item.strip()]
    return [str(value)]


def collect_db_recipes(database_url: str | None = None) -> tuple[bool, list[ExistingRecipe], str | None]:
    database_url = database_url or os.getenv("DATABASE_URL") or "postgresql://aifood:aifood@localhost:5432/aifood"
    try:
        from sqlalchemy import create_engine, inspect, text
    except Exception as exc:  # pragma: no cover - depends on local env
        return False, [], f"sqlalchemy_unavailable:{exc}"

    try:
        engine = create_engine(database_url, future=True)
        with engine.connect() as conn:
            inspector = inspect(conn)
            tables = set(inspector.get_table_names())
            if "recipes" not in tables:
                return False, [], "recipes table not found"
            columns = {column["name"] for column in inspector.get_columns("recipes")}
            select_columns = [
                "id",
                "title",
                "display_title" if "display_title" in columns else "NULL as display_title",
                "normalized_title" if "normalized_title" in columns else "title as normalized_title",
                "source_type" if "source_type" in columns else "NULL as source_type",
                "tags" if "tags" in columns else "NULL as tags",
                "meal_type" if "meal_type" in columns else "NULL as meal_type",
                "category" if "category" in columns else "NULL as category",
                "image_url" if "image_url" in columns else "NULL as image_url",
                "hero_image_url" if "hero_image_url" in columns else "NULL as hero_image_url",
                "thumbnail_url" if "thumbnail_url" in columns else "NULL as thumbnail_url",
                "calories_per_serving" if "calories_per_serving" in columns else "NULL as calories_per_serving",
                "protein_g" if "protein_g" in columns else "NULL as protein_g",
                "fat_g" if "fat_g" in columns else "NULL as fat_g",
                "carbs_g" if "carbs_g" in columns else "NULL as carbs_g",
            ]
            recipe_rows = conn.execute(text(f"select {', '.join(select_columns)} from recipes")).mappings().all()
            ingredient_names_by_id: dict[int, list[str]] = defaultdict(list)
            ingredient_count_by_id: Counter[int] = Counter()
            if "recipe_ingredients" in tables:
                ingredient_columns = {column["name"] for column in inspector.get_columns("recipe_ingredients")}
                name_column = "name" if "name" in ingredient_columns else "display_name" if "display_name" in ingredient_columns else None
                if name_column and "recipe_id" in ingredient_columns:
                    rows = conn.execute(text(f"select recipe_id, {name_column} as name from recipe_ingredients")).mappings().all()
                    for row in rows:
                        recipe_id = int(row["recipe_id"])
                        ingredient_count_by_id[recipe_id] += 1
                        if row["name"]:
                            ingredient_names_by_id[recipe_id].append(str(row["name"]))
            step_count_by_id: Counter[int] = Counter()
            if "recipe_steps" in tables:
                step_columns = {column["name"] for column in inspector.get_columns("recipe_steps")}
                if "recipe_id" in step_columns:
                    rows = conn.execute(text("select recipe_id, count(*) as count from recipe_steps group by recipe_id")).mappings().all()
                    for row in rows:
                        step_count_by_id[int(row["recipe_id"])] = int(row["count"])
        recipes = []
        for row in recipe_rows:
            recipe_id = int(row["id"])
            recipes.append(
                ExistingRecipe(
                    id=recipe_id,
                    title=str(row["title"] or ""),
                    display_title=row["display_title"],
                    normalized_title=normalize(row["normalized_title"] or row["title"]),
                    source_type=row["source_type"],
                    tags=parse_tags(row["tags"]),
                    meal_type=row["meal_type"],
                    category=row["category"],
                    has_images=bool(row["image_url"] or row["hero_image_url"] or row["thumbnail_url"]),
                    ingredient_count=int(ingredient_count_by_id[recipe_id]),
                    step_count=int(step_count_by_id[recipe_id]),
                    nutrition_core_complete=all(
                        row[field] is not None
                        for field in ("calories_per_serving", "protein_g", "fat_g", "carbs_g")
                    ),
                    ingredient_names=ingredient_names_by_id[recipe_id],
                )
            )
        return True, recipes, None
    except Exception as exc:
        return False, [], str(exc)


def candidate_summary(candidate: dict[str, Any], index: int) -> dict[str, Any]:
    nutrition = candidate.get("nutrition_per_serving") or {}
    return {
        "candidate_index": index,
        "candidate_title": candidate.get("title"),
        "candidate_normalized_title": normalize(candidate.get("normalized_title") or candidate.get("title")),
        "candidate_meal_type": candidate.get("meal_type"),
        "candidate_category": candidate.get("category"),
        "candidate_tags": candidate.get("tags") or [],
        "candidate_main_ingredients": main_ingredients(candidate),
        "candidate_ingredient_count": len(candidate.get("ingredients") or []),
        "candidate_step_count": len(candidate.get("steps") or []),
        "candidate_nutrition_summary": {
            "kcal": nutrition.get("kcal"),
            "protein_g": nutrition.get("protein_g"),
            "fat_g": nutrition.get("fat_g"),
            "carbs_g": nutrition.get("carbs_g"),
        },
    }


def find_matches(candidate: dict[str, Any], existing: list[ExistingRecipe]) -> list[dict[str, Any]]:
    title = normalize(candidate.get("title"))
    normalized_title = normalize(candidate.get("normalized_title") or candidate.get("title"))
    candidate_ingredients = ingredient_names(candidate)
    matches_by_id: dict[int, dict[str, Any]] = {}
    for db_recipe in existing:
        db_title = normalize(db_recipe.title)
        db_normalized = normalize(db_recipe.normalized_title or db_recipe.title)
        match_type = None
        score = 0.0
        if title and db_title == title:
            match_type = "exact_title"
            score = 1.0
        elif normalized_title and db_normalized == normalized_title:
            match_type = "exact_normalized_title"
            score = 1.0
        else:
            title_score = max(similarity(title, db_title), similarity(normalized_title, db_normalized))
            overlap = ingredient_overlap(candidate_ingredients, db_recipe.ingredient_names)
            if title_score >= 0.82:
                match_type = "close_title"
                score = title_score
            elif title_score >= 0.55 and overlap >= 0.45:
                match_type = "ingredient_overlap"
                score = round((title_score + overlap) / 2, 4)
        if match_type:
            matches_by_id[db_recipe.id] = db_recipe.to_match(match_type, score)
    return sorted(matches_by_id.values(), key=lambda row: (-row["similarity_score"], row["db_id"]))


def is_existing_weaker(candidate: dict[str, Any], match: dict[str, Any]) -> bool:
    return (
        match["db_ingredient_count"] < len(candidate.get("ingredients") or [])
        or match["db_step_count"] < len(candidate.get("steps") or [])
        or not match["db_has_images"]
        or not match["db_nutrition_core_complete"]
        or str(match.get("db_source_type") or "").lower() in {"import", "legacy", "povarenok", "external"}
    )


def compatible_meal_category(candidate: dict[str, Any], match: dict[str, Any]) -> bool:
    meal_ok = not match.get("db_meal_type") or match.get("db_meal_type") == candidate.get("meal_type")
    category_ok = not match.get("db_category") or match.get("db_category") == candidate.get("category")
    return meal_ok or category_ok


def materially_distinct(candidate: dict[str, Any], match: dict[str, Any]) -> bool:
    candidate_title = str(candidate.get("title") or "")
    db_title = str(match.get("db_title") or "")
    proteins_changed = title_keywords(candidate_title, MEAT_WORDS) != title_keywords(db_title, MEAT_WORDS)
    methods_changed = title_keywords(candidate_title, METHOD_WORDS) != title_keywords(db_title, METHOD_WORDS)
    meal_changed = match.get("db_meal_type") and match.get("db_meal_type") != candidate.get("meal_type")
    return bool(proteins_changed or methods_changed or meal_changed)


def proposed_rename(candidate: dict[str, Any]) -> tuple[str, str]:
    title = str(candidate.get("title") or "").strip()
    meal_type = candidate.get("meal_type") or "gold"
    suffix = {
        "breakfast": "для завтрака",
        "lunch": "для обеда",
        "dinner": "для ужина",
        "snack": "для перекуса",
    }.get(meal_type, "Gold V3")
    proposed = f"{title} {suffix}"
    return proposed, normalize(proposed)


def classify_candidate(candidate: dict[str, Any], matches: list[dict[str, Any]]) -> dict[str, Any]:
    if not matches:
        return {"decision": "safe_to_import", "reason": "No exact, close, or ingredient-overlap duplicate found."}

    exact_matches = [
        match for match in matches if match["match_type"] in {"exact_title", "exact_normalized_title"}
    ]
    strongest = matches[0]
    if exact_matches:
        exact = exact_matches[0]
        if is_existing_weaker(candidate, exact):
            return {
                "decision": "candidate_for_future_upgrade",
                "reason": "Same dish exists, but existing DB recipe appears weaker; upgrade is out of scope.",
            }
        if compatible_meal_category(candidate, exact):
            return {
                "decision": "skip_exact_duplicate",
                "reason": "Exact normalized/title duplicate with compatible meal/category.",
            }
        return {
            "decision": "manual_review",
            "reason": "Exact title duplicate has incompatible meal/category metadata.",
        }

    if materially_distinct(candidate, strongest) and strongest["similarity_score"] < 0.92:
        proposed_title, proposed_normalized_title = proposed_rename(candidate)
        return {
            "decision": "rename_and_import_candidate",
            "reason": "Similar title but materially distinct dish or use case.",
            "proposed_title": proposed_title,
            "proposed_normalized_title": proposed_normalized_title,
            "rename_reason": "Add meal/use-case qualifier to remove duplicate risk.",
        }

    if strongest["similarity_score"] >= 0.72:
        return {
            "decision": "manual_review",
            "reason": "Similarity is high but not a clean exact duplicate or safe rename.",
        }

    return {"decision": "safe_to_import", "reason": "Only weak ingredient overlap found."}


def audit(
    candidates: list[dict[str, Any]] | None = None,
    existing: list[ExistingRecipe] | None = None,
    *,
    db_available: bool | None = None,
    db_error: str | None = None,
    write_reports: bool = True,
) -> dict[str, Any]:
    candidates = candidates if candidates is not None else load_candidates()
    if existing is None:
        db_available, existing, db_error = collect_db_recipes()
    elif db_available is None:
        db_available = True

    items = []
    duplicate_risk_count = 0
    for index, candidate in enumerate(candidates, start=1):
        summary = candidate_summary(candidate, index)
        matches = find_matches(candidate, existing)
        if matches:
            duplicate_risk_count += 1
        if not db_available:
            classification = {
                "decision": "manual_review",
                "reason": "DB unavailable; duplicate classification requires current DB.",
            }
        else:
            classification = classify_candidate(candidate, matches)
        decision = classification["decision"]
        if decision not in DECISIONS:
            raise RuntimeError(f"unknown decision: {decision}")
        items.append(
            {
                **summary,
                "duplicate_matches": matches,
                **classification,
            }
        )

    decision_counts = Counter(item["decision"] for item in items)
    import_now_count = decision_counts["safe_to_import"] + decision_counts["rename_and_import_candidate"]
    duplicate_collisions_remain = bool(
        decision_counts["manual_review"]
        or decision_counts["skip_exact_duplicate"]
        or decision_counts["candidate_for_future_upgrade"]
    )
    blocked_for_apply = (
        not db_available
        or decision_counts["manual_review"] > 0
        or duplicate_collisions_remain
        or import_now_count < 10
    )
    recommendation = recommendation_for(decision_counts, blocked_for_apply)
    report = {
        "generated_at": now(),
        "input": str(INPUT.relative_to(ROOT)),
        "read_only": True,
        "db_available": bool(db_available),
        "db_error": db_error,
        "total_candidates": len(candidates),
        "duplicate_risk_count": duplicate_risk_count,
        "decisions": {decision: decision_counts.get(decision, 0) for decision in sorted(DECISIONS)},
        "import_now_count": import_now_count,
        "blocked_for_apply": blocked_for_apply,
        "recommendation": recommendation,
        "items": items,
    }
    if write_reports:
        REPORTS.mkdir(exist_ok=True)
        REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        REPORT_MD.write_text(render(report), encoding="utf-8")
        maybe_write_plan(report)
    return report


def recommendation_for(decisions: Counter[str], blocked_for_apply: bool) -> str:
    if decisions["manual_review"]:
        return "do_not_apply"
    if decisions["rename_and_import_candidate"]:
        return "prepare_rename_patch"
    if decisions["candidate_for_future_upgrade"]:
        return "prepare_upgrade_sprint"
    if blocked_for_apply:
        return "apply_only_safe_subset_later"
    return "apply_only_safe_subset_later"


def maybe_write_plan(report: dict[str, Any]) -> None:
    if not report["db_available"]:
        return
    if report["blocked_for_apply"]:
        return
    decisions = []
    safe_import_candidates = []
    rename_import_candidates = []
    future_upgrade_candidates = []
    manual_review_candidates = []
    for item in report["items"]:
        row = {
            "candidate_index": item["candidate_index"],
            "candidate_title": item["candidate_title"],
            "decision": item["decision"],
            "matched_db_ids": [match["db_id"] for match in item["duplicate_matches"]],
            "reason": item["reason"],
        }
        if item.get("proposed_title"):
            row["proposed_title"] = item["proposed_title"]
            row["proposed_normalized_title"] = item["proposed_normalized_title"]
        decisions.append(row)
        if item["decision"] == "safe_to_import":
            safe_import_candidates.append(item["candidate_index"])
        elif item["decision"] == "rename_and_import_candidate":
            rename_import_candidates.append(item["candidate_index"])
        elif item["decision"] == "candidate_for_future_upgrade":
            future_upgrade_candidates.append(item["candidate_index"])
        elif item["decision"] == "manual_review":
            manual_review_candidates.append(item["candidate_index"])
    plan = {
        "source": "gold_recipes_30_repaired_candidate.jsonl",
        "total_candidates": report["total_candidates"],
        "decisions": decisions,
        "safe_import_candidates": safe_import_candidates,
        "rename_import_candidates": rename_import_candidates,
        "future_upgrade_candidates": future_upgrade_candidates,
        "manual_review_candidates": manual_review_candidates,
    }
    if has_source_leakage(plan):
        raise RuntimeError("duplicate resolution plan contains source leakage")
    PLAN_JSON.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def render(report: dict[str, Any]) -> str:
    lines = [
        "# Sprint 1.3D Gold V3 Duplicate Resolution",
        "",
        f"Generated: `{report['generated_at']}`",
        f"Input: `{report['input']}`",
        f"Read-only: `{report['read_only']}`",
        f"DB available: `{report['db_available']}`",
        f"DB error: `{report['db_error']}`",
        f"total_candidates: `{report['total_candidates']}`",
        f"duplicate_risk_count: `{report['duplicate_risk_count']}`",
        f"import_now_count: `{report['import_now_count']}`",
        f"blocked_for_apply: `{report['blocked_for_apply']}`",
        f"recommendation: `{report['recommendation']}`",
        "",
        "## Decisions",
        "",
    ]
    for decision, count in report["decisions"].items():
        lines.append(f"- {decision}: `{count}`")
    lines.extend(["", "## Candidates", ""])
    for item in report["items"]:
        match_bits = ", ".join(
            f"{match['db_id']}:{match['match_type']}:{match['similarity_score']}"
            for match in item["duplicate_matches"][:5]
        )
        if not match_bits:
            match_bits = "none"
        lines.append(
            f"- {item['candidate_index']}. {item['candidate_title']}: "
            f"decision=`{item['decision']}`, matches=`{match_bits}`, reason=`{item['reason']}`"
        )
        if item.get("proposed_title"):
            lines.append(f"  proposed_title=`{item['proposed_title']}`")
    return "\n".join(lines) + "\n"


def main() -> int:
    report = audit()
    print(f"Wrote {REPORT_MD}")
    return 0 if report["total_candidates"] == 30 else 1


if __name__ == "__main__":
    raise SystemExit(main())
