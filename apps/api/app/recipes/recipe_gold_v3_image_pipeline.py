"""Stage IMG: Gold V3 recipe image generation pipeline (plan + safety guards)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.recipes.image_generation_config import (
    DEFAULT_ALLOWLIST_IDS,
    ESTIMATED_COST_PER_IMAGE_USD,
    REQUIRED_DERIVATIVE_FILES,
    STYLE_VERSION,
    estimate_batch_cost_usd,
    validate_max_cost_usd,
)
from app.recipes.recipe_gold_v3_importer import is_gold_v3_import_recipe

MASTER_PHOTO_PROMPT = """Create one photorealistic master food image for the PlanAm family meal-planning app.

Dish: {title}
Meal type: {meal_type}
Main ingredients: {ingredients}
Visual description: {short_visual_description}

PlanAm visual system (Gold V3):
- Modern homemade food on one consistent light ceramic dinnerware set.
- Beautiful bright home kitchen background with minimal clutter.
- Appetizing presentation with clean composition and good camera angle.
- Warm, fresh, natural daylight — not studio drama.
- Same visual language across all PlanAm recipe images.

Tableware:
- Light neutral ceramic from one modern home set (warm white / milk white / light beige).
- No patterns, no random different plates.
- Use: {recommended_vessel}

Background:
- Consistent bright home kitchen countertop or light wood/stone surface.
- Minimal, uncluttered, family-home feeling.

Composition:
- {camera_angle}
- The dish is the clear main subject; textures and ingredients visible.
- Slight natural imperfection is welcome.

Restrictions:
- no text, watermark, logo, collage
- no packaging
- no people, no hands
- no excessive garnish or random objects
- no fine-dining restaurant look
- no plastic stock-photo look"""

NEGATIVE_PROMPT_REFERENCE = (
    "text, watermark, logo, packaging, hands, people, clutter, messy table, "
    "plastic look, stock photo, restaurant fine dining, dramatic studio lighting, "
    "random plates, bright patterns, branded items, collage"
)

VESSEL_MAPPINGS: list[dict[str, str]] = [
    {
        "dish_type": "soup",
        "recommended_vessel": "deep ceramic bowl from the PlanAm neutral dinnerware set",
        "camera_angle": "3/4 angle, dish centered, slight depth showing broth surface",
    },
    {
        "dish_type": "porridge",
        "recommended_vessel": "medium ceramic bowl from the PlanAm neutral dinnerware set",
        "camera_angle": "slight top angle (about 25 degrees), showing texture",
    },
    {
        "dish_type": "salad",
        "recommended_vessel": "shallow ceramic bowl or flat plate from the PlanAm set",
        "camera_angle": "top or 3/4 angle, fresh colors visible",
    },
    {
        "dish_type": "casserole",
        "recommended_vessel": "flat dinner plate with a neat portion from the baking dish",
        "camera_angle": "3/4 angle, golden top texture visible",
    },
    {
        "dish_type": "chicken_with_side",
        "recommended_vessel": "flat dinner plate from the PlanAm neutral dinnerware set",
        "camera_angle": "3/4 angle, protein and side clearly visible",
    },
    {
        "dish_type": "cutlet",
        "recommended_vessel": "flat dinner plate from the PlanAm neutral dinnerware set",
        "camera_angle": "3/4 angle, golden patties and vegetable side visible",
    },
    {
        "dish_type": "default",
        "recommended_vessel": "flat dinner plate from the PlanAm neutral dinnerware set",
        "camera_angle": "3/4 angle, dish as clear main subject",
    },
]

DISH_TYPE_PATTERNS: list[tuple[str, str]] = [
    ("soup", r"суп|борщ|щи|уха|бульон|солянк|харч|пюре"),
    ("porridge", r"каш|крупа|овсян|гречн|пшён|перлов|манн"),
    ("salad", r"салат|винегрет"),
    ("casserole", r"запекан"),
    ("cutlet", r"котлет"),
    ("chicken_with_side", r"курин|грудк|окороч|индейк"),
]


class ImagePipelineError(ValueError):
    pass


class IdNotAllowedError(ImagePipelineError):
    pass


@dataclass
class RecipeImageTarget:
    recipe_id: int
    title: str
    meal_type: str
    category: str
    ingredients: list[Any]
    hero_image_url: str | None
    image_url: str | None
    thumbnail_url: str | None
    tags: list[Any]
    source_type: str
    is_gold_v3: bool
    hero_file_exists: bool
    derivatives_complete: bool
    status: str
    skip_reason: str | None = None
    master_prompt: str | None = None
    estimated_cost_usd: float = ESTIMATED_COST_PER_IMAGE_USD

    def as_dict(self) -> dict[str, Any]:
        return {
            "recipe_id": self.recipe_id,
            "title": self.title,
            "meal_type": self.meal_type,
            "category": self.category,
            "is_gold_v3": self.is_gold_v3,
            "hero_image_url": self.hero_image_url,
            "hero_file_exists": self.hero_file_exists,
            "derivatives_complete": self.derivatives_complete,
            "status": self.status,
            "skip_reason": self.skip_reason,
            "estimated_cost_usd": self.estimated_cost_usd,
            "master_prompt_preview": (self.master_prompt or "")[:120],
        }


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def infer_dish_type(title: str, meal_type: str, category: str) -> str:
    text = normalize_text(title)
    if category == "soup" or re.search(DISH_TYPE_PATTERNS[0][1], text):
        return "soup"
    for dish_type, pattern in DISH_TYPE_PATTERNS[1:]:
        if re.search(pattern, text):
            return dish_type
    if meal_type == "breakfast" or category in {"breakfast", "quick"}:
        return "porridge"
    return "default"


def resolve_vessel_mapping(title: str, meal_type: str, category: str) -> dict[str, str]:
    dish_type = infer_dish_type(title, meal_type, category)
    for row in VESSEL_MAPPINGS:
        if row["dish_type"] == dish_type:
            return row
    return VESSEL_MAPPINGS[-1]


def ingredient_names(ingredients: list[Any], *, limit: int = 6) -> str:
    names: list[str] = []
    for item in ingredients:
        if isinstance(item, dict):
            name = str(item.get("name") or item.get("shopping_name") or "").strip()
            if name:
                names.append(name)
        elif isinstance(item, str) and item.strip():
            names.append(item.strip())
        if len(names) >= limit:
            break
    return ", ".join(names) if names else "common home ingredients"


def short_visual_description(title: str, meal_type: str, category: str) -> str:
    dish_type = infer_dish_type(title, meal_type, category)
    templates = {
        "soup": "Homemade soup in a deep bowl, steam visible, rustic family portion.",
        "porridge": "Warm grain dish in a bowl, creamy texture, colorful vegetables.",
        "salad": "Fresh salad with visible ingredients, light clean presentation.",
        "casserole": "Baked casserole portion with golden top, comfort-food feel.",
        "chicken_with_side": "Chicken dish with sides on one plate, hearty family dinner.",
        "cutlet": "Golden homemade cutlets with vegetable side on a flat plate.",
        "default": f"Homemade «{title}» on neutral ceramic, warm family meal.",
    }
    return templates.get(dish_type, templates["default"])


def build_master_prompt(recipe: dict[str, Any]) -> str:
    title = str(recipe.get("title") or recipe.get("display_title") or "").strip()
    meal_type = str(recipe.get("meal_type") or "dinner")
    category = str(recipe.get("category") or "main")
    ingredients = recipe.get("ingredients") or []
    vessel = resolve_vessel_mapping(title, meal_type, category)
    visual = str(
        recipe.get("short_visual_description")
        or short_visual_description(title, meal_type, category)
    )
    return MASTER_PHOTO_PROMPT.format(
        title=title,
        meal_type=meal_type,
        ingredients=ingredient_names(ingredients),
        short_visual_description=visual,
        recommended_vessel=vessel["recommended_vessel"],
        camera_angle=vessel["camera_angle"],
    )


def parse_ids_csv(value: str) -> list[int]:
    ids: list[int] = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        ids.append(int(part))
    return ids


def load_created_ids_from_report(path: Path) -> list[int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    created = data.get("created") or []
    ids: list[int] = []
    for row in created:
        if isinstance(row, dict) and row.get("id") is not None:
            ids.append(int(row["id"]))
    return ids


def validate_ids_allowed(
    recipe_ids: list[int],
    *,
    explicit_ids: bool,
    allowlist: tuple[int, ...] = DEFAULT_ALLOWLIST_IDS,
) -> None:
    if not recipe_ids:
        raise ImagePipelineError("no_recipe_ids")
    if explicit_ids:
        return
    allowset = set(allowlist)
    outside = [rid for rid in recipe_ids if rid not in allowset]
    if outside:
        raise IdNotAllowedError(
            f"recipe IDs outside default allowlist {list(allowlist)}: {outside}. "
            "Pass --ids explicitly to override."
        )


def build_public_image_urls(
    recipe_id: int,
    *,
    public_base: str = "/recipe-images",
) -> dict[str, str]:
    base = f"{public_base.rstrip('/')}/{recipe_id}"
    return {
        "hero_image_url": f"{base}/hero.webp",
        "image_url": f"{base}/card_800.webp",
        "thumbnail_url": f"{base}/thumb_400.webp",
    }


def recipe_image_folder(recipe_id: int, images_dir: Path) -> Path:
    return images_dir / str(recipe_id)


def hero_file_path(recipe_id: int, images_dir: Path) -> Path:
    return recipe_image_folder(recipe_id, images_dir) / "hero.webp"


def derivatives_complete(recipe_id: int, images_dir: Path) -> bool:
    folder = recipe_image_folder(recipe_id, images_dir)
    return folder.is_dir() and all((folder / name).is_file() for name in REQUIRED_DERIVATIVE_FILES)


def has_existing_hero(
    *,
    hero_image_url: str | None,
    recipe_id: int,
    images_dir: Path,
) -> bool:
    if hero_image_url:
        return True
    return hero_file_path(recipe_id, images_dir).is_file()


def recipe_to_prompt_dict(recipe: Any) -> dict[str, Any]:
    return {
        "title": recipe.title,
        "display_title": getattr(recipe, "display_title", None),
        "meal_type": recipe.meal_type,
        "category": recipe.category,
        "ingredients": recipe.ingredients or [],
    }


def fetch_gold_v3_recipes_by_ids(session: Any, recipe_ids: list[int]) -> dict[int, Any]:
    from app.models.recipe import Recipe

    rows = session.query(Recipe).filter(Recipe.id.in_(recipe_ids)).all()
    return {int(r.id): r for r in rows}


def plan_image_generation(
    session: Any,
    recipe_ids: list[int],
    *,
    images_dir: Path,
    force: bool = False,
    explicit_ids: bool = False,
    allowlist: tuple[int, ...] = DEFAULT_ALLOWLIST_IDS,
) -> dict[str, Any]:
    validate_ids_allowed(recipe_ids, explicit_ids=explicit_ids, allowlist=allowlist)
    by_id = fetch_gold_v3_recipes_by_ids(session, recipe_ids)

    targets: list[RecipeImageTarget] = []
    errors_by_code: dict[str, int] = {}
    warnings_by_code: dict[str, int] = {}

    for rid in recipe_ids:
        recipe = by_id.get(rid)
        if recipe is None:
            errors_by_code["recipe_not_found"] = errors_by_code.get("recipe_not_found", 0) + 1
            targets.append(
                RecipeImageTarget(
                    recipe_id=rid,
                    title="",
                    meal_type="",
                    category="",
                    ingredients=[],
                    hero_image_url=None,
                    image_url=None,
                    thumbnail_url=None,
                    tags=[],
                    source_type="",
                    is_gold_v3=False,
                    hero_file_exists=False,
                    derivatives_complete=False,
                    status="failed",
                    skip_reason="recipe_not_found",
                )
            )
            continue

        gold_v3 = is_gold_v3_import_recipe(recipe.tags, recipe.source_type)
        if not gold_v3:
            errors_by_code["not_gold_v3_import"] = errors_by_code.get("not_gold_v3_import", 0) + 1
            targets.append(
                RecipeImageTarget(
                    recipe_id=rid,
                    title=recipe.title,
                    meal_type=recipe.meal_type,
                    category=recipe.category,
                    ingredients=recipe.ingredients or [],
                    hero_image_url=recipe.hero_image_url,
                    image_url=recipe.image_url,
                    thumbnail_url=recipe.thumbnail_url,
                    tags=recipe.tags if isinstance(recipe.tags, list) else [],
                    source_type=recipe.source_type,
                    is_gold_v3=False,
                    hero_file_exists=hero_file_path(rid, images_dir).is_file(),
                    derivatives_complete=derivatives_complete(rid, images_dir),
                    status="failed",
                    skip_reason="not_gold_v3_import",
                )
            )
            continue

        hero_exists = has_existing_hero(
            hero_image_url=recipe.hero_image_url,
            recipe_id=rid,
            images_dir=images_dir,
        )
        deriv_ok = derivatives_complete(rid, images_dir)
        prompt = build_master_prompt(recipe_to_prompt_dict(recipe))

        if hero_exists and not force:
            status = "skip_existing"
            skip_reason = "hero_already_present"
            warnings_by_code["idempotent_skip"] = warnings_by_code.get("idempotent_skip", 0) + 1
        else:
            status = "would_generate"
            skip_reason = None

        targets.append(
            RecipeImageTarget(
                recipe_id=rid,
                title=recipe.title,
                meal_type=recipe.meal_type,
                category=recipe.category,
                ingredients=recipe.ingredients or [],
                hero_image_url=recipe.hero_image_url,
                image_url=recipe.image_url,
                thumbnail_url=recipe.thumbnail_url,
                tags=recipe.tags if isinstance(recipe.tags, list) else [],
                source_type=recipe.source_type,
                is_gold_v3=True,
                hero_file_exists=hero_file_path(rid, images_dir).is_file(),
                derivatives_complete=deriv_ok,
                status=status,
                skip_reason=skip_reason,
                master_prompt=prompt,
            )
        )

    to_generate = [t for t in targets if t.status == "would_generate"]
    to_skip = [t for t in targets if t.status == "skip_existing"]
    failed = [t for t in targets if t.status == "failed"]
    generate_count = len(to_generate)
    estimated_total = estimate_batch_cost_usd(generate_count)
    idempotent_full_skip = (
        not failed
        and generate_count == 0
        and len(to_skip) == len(recipe_ids)
        and len(recipe_ids) > 0
    )
    ok = not errors_by_code and (generate_count > 0 or idempotent_full_skip)

    return {
        "ok": ok,
        "style_version": STYLE_VERSION,
        "recipe_ids": recipe_ids,
        "allowlist": list(allowlist),
        "explicit_ids": explicit_ids,
        "force": force,
        "targets": [t.as_dict() for t in targets],
        "to_generate_count": generate_count,
        "to_skip_count": len(to_skip),
        "failed_count": len(failed),
        "estimated_cost_usd": estimated_total,
        "cost_per_image_usd": ESTIMATED_COST_PER_IMAGE_USD,
        "idempotent_full_skip": idempotent_full_skip,
        "errors_by_code": errors_by_code,
        "warnings_by_code": warnings_by_code,
        "to_generate": to_generate,
        "to_skip": to_skip,
        "failed": failed,
    }


def apply_image_urls_to_recipe(session: Any, recipe_id: int, urls: dict[str, str]) -> None:
    from app.models.recipe import Recipe

    recipe = session.get(Recipe, recipe_id)
    if recipe is None:
        raise ImagePipelineError(f"recipe {recipe_id} not found during apply")
    recipe.hero_image_url = urls["hero_image_url"]
    recipe.image_url = urls["image_url"]
    recipe.thumbnail_url = urls["thumbnail_url"]
    session.commit()


def check_apply_guards(
    *,
    apply_mode: bool,
    max_cost_usd: float | None,
    estimated_cost_usd: float,
    api_configured: bool,
) -> tuple[bool, str | None]:
    if not apply_mode:
        return True, None
    if not api_configured:
        return False, "api_key_missing"
    ok, code = validate_max_cost_usd(estimated_cost_usd, max_cost_usd)
    if not ok:
        return False, code
    return True, None
