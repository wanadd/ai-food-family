"""CRUD for recipe_collections and collection_recipes."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.recipe_engine import CollectionRecipe, RecipeCollection


class RecipeCollectionRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, collection_id: int) -> RecipeCollection | None:
        return self._db.get(RecipeCollection, collection_id)

    def list_for_user(self, user_id: int) -> list[RecipeCollection]:
        return (
            self._db.query(RecipeCollection)
            .filter(
                RecipeCollection.visibility == "personal",
                RecipeCollection.owner_user_id == user_id,
            )
            .order_by(RecipeCollection.position.asc(), RecipeCollection.id.asc())
            .all()
        )

    def list_for_family(self, family_id: int) -> list[RecipeCollection]:
        return (
            self._db.query(RecipeCollection)
            .filter(
                RecipeCollection.visibility == "family",
                RecipeCollection.owner_family_id == family_id,
            )
            .order_by(RecipeCollection.position.asc(), RecipeCollection.id.asc())
            .all()
        )

    def list_system(self) -> list[RecipeCollection]:
        return (
            self._db.query(RecipeCollection)
            .filter(RecipeCollection.visibility == "system")
            .order_by(RecipeCollection.position.asc(), RecipeCollection.id.asc())
            .all()
        )

    def create(self, collection: RecipeCollection) -> RecipeCollection:
        self._db.add(collection)
        self._db.flush()
        return collection

    def update(self, collection: RecipeCollection) -> RecipeCollection:
        self._db.add(collection)
        self._db.flush()
        return collection

    def delete(self, collection: RecipeCollection) -> None:
        self._db.delete(collection)
        self._db.flush()


class CollectionRecipeRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_for_collection(self, collection_id: int) -> list[CollectionRecipe]:
        return (
            self._db.query(CollectionRecipe)
            .filter(CollectionRecipe.collection_id == collection_id)
            .order_by(CollectionRecipe.position.asc(), CollectionRecipe.id.asc())
            .all()
        )

    def get_link(
        self, collection_id: int, recipe_id: int
    ) -> CollectionRecipe | None:
        return (
            self._db.query(CollectionRecipe)
            .filter(
                CollectionRecipe.collection_id == collection_id,
                CollectionRecipe.recipe_id == recipe_id,
            )
            .one_or_none()
        )

    def add(self, link: CollectionRecipe) -> CollectionRecipe:
        self._db.add(link)
        self._db.flush()
        return link

    def delete(self, link: CollectionRecipe) -> None:
        self._db.delete(link)
        self._db.flush()

    def delete_by_ids(self, collection_id: int, recipe_id: int) -> bool:
        link = self.get_link(collection_id, recipe_id)
        if link is None:
            return False
        self.delete(link)
        return True
