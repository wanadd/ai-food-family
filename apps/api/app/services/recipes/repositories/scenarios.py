"""CRUD for recipe_scenarios."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.recipe_engine import RecipeScenario


class RecipeScenarioRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_for_recipe(self, recipe_id: int) -> list[RecipeScenario]:
        return (
            self._db.query(RecipeScenario)
            .filter(RecipeScenario.recipe_id == recipe_id)
            .all()
        )

    def list_by_scenario(self, scenario: str, *, limit: int = 200) -> list[RecipeScenario]:
        return (
            self._db.query(RecipeScenario)
            .filter(RecipeScenario.scenario == scenario)
            .limit(limit)
            .all()
        )

    def get(self, recipe_id: int, scenario: str) -> RecipeScenario | None:
        return (
            self._db.query(RecipeScenario)
            .filter(
                RecipeScenario.recipe_id == recipe_id,
                RecipeScenario.scenario == scenario,
            )
            .one_or_none()
        )

    def upsert(self, row: RecipeScenario) -> RecipeScenario:
        existing = self.get(row.recipe_id, row.scenario)
        if existing is not None:
            existing.score = row.score
            existing.source = row.source
            self._db.flush()
            return existing
        self._db.add(row)
        self._db.flush()
        return row

    def delete_for_recipe(self, recipe_id: int, *, source: str | None = None) -> int:
        q = self._db.query(RecipeScenario).filter(RecipeScenario.recipe_id == recipe_id)
        if source is not None:
            q = q.filter(RecipeScenario.source == source)
        count = q.delete(synchronize_session=False)
        self._db.flush()
        return count

    def delete(self, row: RecipeScenario) -> None:
        self._db.delete(row)
        self._db.flush()
