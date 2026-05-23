#!/usr/bin/env python3
"""Seed PlanAm recipe catalog (food, drinks, events). Run from repo root."""

from __future__ import annotations

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
API_ROOT = os.path.join(ROOT, "apps", "api")
sys.path.insert(0, API_ROOT)

os.environ.setdefault("DATABASE_URL", os.environ.get("DATABASE_URL", ""))

from app.database import SessionLocal, init_db  # noqa: E402
from app.data.recipe_catalog_seed import CATALOG_RECIPES  # noqa: E402
from app.models.recipe import Recipe  # noqa: E402
from app.services.recipe_storage import persist_recipe_structure  # noqa: E402


def seed(*, force: bool = False) -> int:
    init_db()
    db = SessionLocal()
    try:
        existing = db.query(Recipe).count()
        if existing > 0 and not force:
            print(f"Skip: {existing} recipes already in DB (use --force to add catalog)")
            return 0

        added = 0
        for data in CATALOG_RECIPES:
            title = data["title"]
            found = db.query(Recipe).filter(Recipe.title == title).one_or_none()
            if found and not force:
                continue
            if found:
                recipe = found
            else:
                recipe = Recipe(
                    title=data["title"],
                    description=data.get("description", ""),
                    meal_type=data["meal_type"],
                    category=data.get("category", "main"),
                    cooking_time_minutes=data.get("cooking_time_minutes", 30),
                    prep_time_minutes=data.get("prep_time_minutes"),
                    servings=data.get("servings", 4),
                    difficulty=data.get("difficulty", "easy"),
                    calories_per_serving=data.get("calories_per_serving"),
                    protein_g=data.get("protein_g"),
                    is_drink=data.get("is_drink", False),
                    is_alcoholic=data.get("is_alcoholic", False),
                    alcohol_percent=data.get("alcohol_percent"),
                    caffeine_mg=data.get("caffeine_mg"),
                    sugar_g=data.get("sugar_g"),
                    suitable_for_children=data.get("suitable_for_children", True),
                    suitable_for_sport=data.get("suitable_for_sport", False),
                    suitable_for_event=data.get("suitable_for_event", False),
                    source_type=data.get("source_type", "import"),
                    diets=data.get("diets", []),
                    tags=data.get("tags", []),
                )
                db.add(recipe)
                db.flush()

            persist_recipe_structure(
                db,
                recipe,
                ingredients=data["ingredients"],
                steps=data["steps"],
                tags=data.get("tags"),
                allergens=data.get("allergens"),
                restrictions=data.get("restrictions"),
            )
            added += 1

        db.commit()
        total = db.query(Recipe).count()
        print(f"Seeded {added} recipes; total in DB: {total}")
        return added
    finally:
        db.close()


if __name__ == "__main__":
    force = "--force" in sys.argv
    seed(force=force)
