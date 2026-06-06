"""Shared utilities for PlanAm V1 recipe image pipeline.

Vessel mapping, visual descriptions, and master prompt building.
One master image per recipe — hero/card/thumb are derived crops.
"""

from __future__ import annotations

import re
from typing import Any


STYLE_PROFILE = "planam_v1_home_kitchen"

MASTER_PROMPT_TEMPLATE = """Create one photorealistic master food image for the PlanAm family meal-planning app.

Dish: {title}
Meal type: {meal_type}
Main ingredients: {ingredients}
Visual description: {short_visual_description}

PlanAm visual system:
- The dish should look like it was cooked at home in a real kitchen.
- The image must feel real, warm, appetizing, and believable.
- The food should not look overly perfect or artificial.
- It should be carefully and beautifully served, but still homemade.
- The dish must belong to the same visual world as other PlanAm recipe images.

Tableware:
- Use tableware from one consistent modern home ceramic dinnerware set.
- Light neutral ceramic: warm white, milk white, or very light beige.
- No bright patterns.
- No random different plates.
- Choose the appropriate item from the same set:
  {recommended_vessel}

Background:
- Consistent bright home kitchen background.
- Light kitchen countertop, light wood, or light stone surface.
- Minimal uncluttered background.
- Same family-home kitchen feeling across all recipe images.

Lighting:
- Soft natural daylight from a kitchen window.
- Gentle shadows.
- Fresh, clean, warm tone.
- Not dramatic studio lighting.

Composition:
- {camera_angle}
- The dish is the clear main subject.
- Ingredients and texture should be visible.
- Composition should be premium but real.
- Slight natural imperfection is welcome.
- The image should make the user want to cook this dish.

Restrictions:
- no text
- no watermark
- no logo
- no collage
- no packaging
- no people
- no hands
- no excessive garnish
- no fine-dining restaurant presentation
- no plastic stock-photo look
- no messy table"""


VESSEL_MAPPINGS: list[dict[str, str]] = [
    {
        "dish_type": "soup",
        "meal_type": "lunch",
        "category": "soup",
        "recommended_vessel": "deep ceramic bowl from the PlanAm neutral dinnerware set",
        "camera_angle": "3/4 angle, dish centered, slight depth showing broth surface",
    },
    {
        "dish_type": "porridge",
        "meal_type": "breakfast",
        "category": "breakfast",
        "recommended_vessel": "medium ceramic bowl from the PlanAm neutral dinnerware set",
        "camera_angle": "slight top angle (about 25 degrees), showing texture of the porridge",
    },
    {
        "dish_type": "pasta",
        "meal_type": "dinner",
        "category": "main",
        "recommended_vessel": "flat dinner plate from the PlanAm neutral dinnerware set",
        "camera_angle": "3/4 angle, pasta twirl or portion visible",
    },
    {
        "dish_type": "chicken_with_side",
        "meal_type": "dinner",
        "category": "main",
        "recommended_vessel": "flat dinner plate from the PlanAm neutral dinnerware set",
        "camera_angle": "3/4 angle, protein and side clearly visible",
    },
    {
        "dish_type": "salad",
        "meal_type": "lunch",
        "category": "salad",
        "recommended_vessel": "shallow ceramic bowl or flat plate from the PlanAm set",
        "camera_angle": "top or 3/4 angle, fresh colors visible",
    },
    {
        "dish_type": "casserole",
        "meal_type": "dinner",
        "category": "main",
        "recommended_vessel": "flat dinner plate with a neat portion from the baking dish",
        "camera_angle": "3/4 angle, golden top texture visible",
    },
    {
        "dish_type": "breakfast",
        "meal_type": "breakfast",
        "category": "quick",
        "recommended_vessel": "small plate or bowl from the PlanAm neutral dinnerware set",
        "camera_angle": "slight top angle, cozy morning light",
    },
    {
        "dish_type": "side",
        "meal_type": "dinner",
        "category": "side",
        "recommended_vessel": "small side plate from the PlanAm neutral dinnerware set",
        "camera_angle": "3/4 angle, simple portion",
    },
    {
        "dish_type": "default",
        "meal_type": "dinner",
        "category": "main",
        "recommended_vessel": "flat dinner plate from the PlanAm neutral dinnerware set",
        "camera_angle": "3/4 angle, dish as clear main subject",
    },
]

DISH_TYPE_PATTERNS: list[tuple[str, str]] = [
    ("soup", r"суп|борщ|щи|уха|бульон|солянк|харч"),
    ("porridge", r"каш|овсян|гречн|пшён|перлов|манн"),
    ("pasta", r"паст|макарон|лапш|спагет"),
    ("salad", r"салат|винегрет"),
    ("casserole", r"запекан"),
    ("chicken_with_side", r"курин|котлет|окороч|грудк"),
]


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def infer_dish_type(title: str, meal_type: str, category: str) -> str:
    text = normalize_text(title)
    if category == "soup" or re.search(DISH_TYPE_PATTERNS[0][1], text):
        return "soup"
    if re.search(r"курин|котлет|окороч|грудк|индейк", text):
        return "chicken_with_side"
    for dish_type, pattern in DISH_TYPE_PATTERNS[1:]:
        if re.search(pattern, text):
            return dish_type
    if meal_type == "breakfast" or category in {"breakfast", "quick"}:
        return "breakfast"
    if category == "salad":
        return "salad"
    if category == "side":
        return "side"
    return "default"


def resolve_vessel_mapping(
    title: str,
    meal_type: str,
    category: str,
) -> dict[str, str]:
    dish_type = infer_dish_type(title, meal_type, category)
    for row in VESSEL_MAPPINGS:
        if row["dish_type"] == dish_type:
            return row
    return VESSEL_MAPPINGS[-1]


def ingredient_names(ingredients: list[Any], *, limit: int = 6) -> str:
    names: list[str] = []
    for item in ingredients:
        if isinstance(item, dict):
            name = str(item.get("name") or "").strip()
            if name:
                names.append(name)
        if len(names) >= limit:
            break
    return ", ".join(names) if names else "common home ingredients"


def short_visual_description(title: str, meal_type: str, category: str) -> str:
    dish_type = infer_dish_type(title, meal_type, category)
    templates = {
        "soup": "Homemade soup in a deep bowl, steam visible, rustic family portion.",
        "porridge": "Warm breakfast porridge, creamy texture, simple home presentation.",
        "pasta": "Pasta with sauce on a flat plate, appetizing home-cooked portion.",
        "salad": "Fresh salad with visible vegetables, light and clean presentation.",
        "casserole": "Baked casserole portion with golden top, comfort-food feel.",
        "chicken_with_side": "Chicken dish with a side on one plate, hearty family dinner.",
        "breakfast": "Simple breakfast on a small plate, cozy morning mood.",
        "side": "Side dish portion on a small plate, complements a main course.",
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
    return MASTER_PROMPT_TEMPLATE.format(
        title=title,
        meal_type=meal_type,
        ingredients=ingredient_names(ingredients),
        short_visual_description=visual,
        recommended_vessel=vessel["recommended_vessel"],
        camera_angle=vessel["camera_angle"],
    )


def build_pilot_row(recipe: dict[str, Any], *, recipe_id: int | None = None) -> dict[str, Any]:
    title = str(recipe.get("title") or "").strip()
    meal_type = str(recipe.get("meal_type") or "dinner")
    category = str(recipe.get("category") or "main")
    vessel = resolve_vessel_mapping(title, meal_type, category)
    return {
        "recipe_id": recipe_id,
        "title": title,
        "meal_type": meal_type,
        "category": category,
        "ingredients": ingredient_names(recipe.get("ingredients") or [], limit=8),
        "short_visual_description": short_visual_description(title, meal_type, category),
        "recommended_vessel": vessel["recommended_vessel"],
        "camera_angle": vessel["camera_angle"],
        "dish_type": vessel["dish_type"],
        "style_profile": STYLE_PROFILE,
        "master_prompt": build_master_prompt(recipe),
        "status": "planned",
        "estimated_calls": 2,
        "actual_cost": None,
        "actual_tokens": None,
        "quality_score": None,
        "decision": None,
    }
