"""Collection domain foundation for the Recipe Engine.

This module hosts:

  - ``CollectionVisibility`` — the closed enum of visibility scopes
    (``SYSTEM`` / ``PERSONAL`` / ``FAMILY``) per
    ``docs/RECIPE_ENGINE_V1.md`` § 2.3.3.
  - ``CollectionRef`` and ``CollectionDetail`` — frozen dataclass DTOs
    for the internal service layer.
  - ``CollectionMapper`` — ORM → DTO mapping helpers. Stubs today; in
    Sprint 2 they wrap the ``recipe_collections`` and
    ``collection_recipes`` tables introduced by migration **M4**.
  - ``CollectionService`` — façade over the (future) collections data
    access. Sprint 1 ships read-only stubs that return empty results;
    write methods raise ``NotImplementedError`` until the migration and
    feature flag are in place (see commit 8 and Sprint 2 roadmap).

Sprint 1 constraint: no migrations, no API route consumes this module.
The only purpose is to lock down the type surface so future commits and
the Sprint 2 routes can be added without churn.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable

from sqlalchemy.orm import Session

from app.config import settings
from app.models.recipe_engine import CollectionRecipe, RecipeCollection
from app.models.user import User
from app.services.app_scope import AppScope
from app.services.recipes.repositories.collections import (
    CollectionRecipeRepository,
    RecipeCollectionRepository,
)


class CollectionVisibility(str, Enum):
    """Visibility scope for a recipe collection."""

    SYSTEM = "system"
    PERSONAL = "personal"
    FAMILY = "family"


# Sprint 4 naming compatibility (constants referenced by the architecture
# spec). Values match Pydantic ``VisibilityLiteral`` in
# ``apps/api/app/schemas/recipe_collection.py``.
SYSTEM_COLLECTION = CollectionVisibility.SYSTEM.value
PERSONAL_COLLECTION = CollectionVisibility.PERSONAL.value
FAMILY_COLLECTION = CollectionVisibility.FAMILY.value


# Internal type alias requested by Sprint 4: "CollectionTypes".
# In this codebase we model it as the same enum as visibility.
CollectionTypes = CollectionVisibility


@dataclass(frozen=True)
class CollectionRef:
    """Lightweight collection reference for lists & menus."""

    id: int
    name: str
    visibility: CollectionVisibility
    description: str = ""
    emoji: str | None = None
    color: str | None = None
    is_pinned: bool = False
    is_dynamic: bool = False
    recipes_count: int = 0
    owner_user_id: int | None = None
    owner_family_id: int | None = None


@dataclass(frozen=True)
class CollectionDetail:
    """Full collection view including its recipes (IDs only at this stage).

    Sprint 2 enriches this with full ``RecipeSummary`` rows; in Sprint 1
    we only carry IDs to avoid a circular import with the mapper.
    """

    ref: CollectionRef
    recipe_ids: tuple[int, ...] = field(default_factory=tuple)


def _ref_from_orm(
    row: RecipeCollection, *, recipes_count: int | None = None
) -> CollectionRef:
    count = recipes_count
    if count is None and not row.is_dynamic:
        count = len(row.recipe_links)
    return CollectionRef(
        id=row.id,
        name=row.name,
        visibility=CollectionVisibility(row.visibility),
        description=row.description or "",
        emoji=row.emoji,
        color=row.color,
        is_pinned=row.is_pinned,
        is_dynamic=row.is_dynamic,
        recipes_count=count or 0,
        owner_user_id=row.owner_user_id,
        owner_family_id=row.owner_family_id,
    )


class CollectionMapper:
    """ORM → DTO conversion for collections.

    The real ORM models (``RecipeCollection``, ``CollectionRecipe``) do not
    exist yet — migration **M4** introduces them. The methods below are
    typed shape stubs so future commits can fill in without touching the
    caller code.
    """

    @staticmethod
    def to_ref_from_dict(payload: dict) -> CollectionRef:
        """Convert a plain dictionary into a ``CollectionRef``.

        Useful for the upcoming seed of system collections (commit added
        in Sprint 2, stage 4) and for ad-hoc tests in Sprint 1.
        """

        return CollectionRef(
            id=int(payload["id"]),
            name=str(payload["name"]),
            visibility=CollectionVisibility(payload.get("visibility", "system")),
            description=str(payload.get("description", "")),
            emoji=payload.get("emoji"),
            color=payload.get("color"),
            is_pinned=bool(payload.get("is_pinned", False)),
            is_dynamic=bool(payload.get("is_dynamic", False)),
            recipes_count=int(payload.get("recipes_count", 0)),
            owner_user_id=payload.get("owner_user_id"),
            owner_family_id=payload.get("owner_family_id"),
        )

    @staticmethod
    def to_detail_from_dict(payload: dict) -> CollectionDetail:
        ref = CollectionMapper.to_ref_from_dict(payload)
        recipe_ids = tuple(int(rid) for rid in payload.get("recipe_ids", ()))
        return CollectionDetail(ref=ref, recipe_ids=recipe_ids)


class CollectionService:
    """Read/write façade for recipe collections."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._collections = RecipeCollectionRepository(db)
        self._links = CollectionRecipeRepository(db)

    def _enabled(self) -> bool:
        return bool(settings.recipe_collections)

    def _can_write(
        self, row: RecipeCollection, user: User, scope: AppScope | None
    ) -> bool:
        if row.visibility == CollectionVisibility.SYSTEM.value:
            return False
        if row.visibility == CollectionVisibility.PERSONAL.value:
            return row.owner_user_id == user.id
        if row.visibility == CollectionVisibility.FAMILY.value:
            return (
                scope is not None
                and scope.family_id is not None
                and row.owner_family_id == scope.family_id
            )
        return False

    def list_visible(
        self, user: User, scope: AppScope | None = None
    ) -> list[CollectionRef]:
        if not self._enabled():
            return []

        rows: list[RecipeCollection] = list(self._collections.list_system())
        rows.extend(self._collections.list_for_user(user.id))
        if scope is not None and scope.family_id is not None:
            rows.extend(self._collections.list_for_family(scope.family_id))

        return [_ref_from_orm(r) for r in rows]

    def get(
        self,
        collection_id: int,
        *,
        user: User,
        scope: AppScope | None = None,
    ) -> CollectionDetail | None:
        if not self._enabled():
            return None

        row = self._collections.get(collection_id)
        if row is None:
            return None

        if row.is_dynamic:
            recipe_ids = self.resolve_dynamic(
                _ref_from_orm(row), user=user, scope=scope
            )
            return CollectionDetail(
                ref=_ref_from_orm(row, recipes_count=len(recipe_ids)),
                recipe_ids=recipe_ids,
            )

        links = self._links.list_for_collection(collection_id)
        ref = _ref_from_orm(row, recipes_count=len(links))
        return CollectionDetail(
            ref=ref, recipe_ids=tuple(link.recipe_id for link in links)
        )

    def resolve_dynamic(
        self,
        collection: CollectionRef,
        *,
        user: User,
        scope: AppScope | None = None,
    ) -> tuple[int, ...]:
        _ = (collection, user, scope)
        return ()

    def create(
        self,
        *,
        name: str,
        visibility: CollectionVisibility,
        user: User,
        scope: AppScope | None = None,
        description: str = "",
        emoji: str | None = None,
        color: str | None = None,
    ) -> CollectionRef:
        if not self._enabled():
            raise NotImplementedError("recipe_collections feature flag is disabled")

        owner_user_id: int | None = None
        owner_family_id: int | None = None

        if visibility == CollectionVisibility.PERSONAL:
            owner_user_id = user.id
        elif visibility == CollectionVisibility.FAMILY:
            if scope is None or scope.family_id is None:
                raise ValueError("Family collection requires family scope")
            owner_family_id = scope.family_id
        else:
            raise ValueError("Cannot create system collections via service")

        row = RecipeCollection(
            name=name,
            visibility=visibility.value,
            description=description,
            emoji=emoji,
            color=color,
            owner_user_id=owner_user_id,
            owner_family_id=owner_family_id,
        )
        self._collections.create(row)
        self._db.commit()
        self._db.refresh(row)
        return _ref_from_orm(row)

    def update(
        self,
        collection_id: int,
        *,
        user: User,
        scope: AppScope | None = None,
        **changes: object,
    ) -> CollectionRef | None:
        if not self._enabled():
            raise NotImplementedError("recipe_collections feature flag is disabled")

        row = self._collections.get(collection_id)
        if row is None or not self._can_write(row, user, scope):
            return None

        for key, value in changes.items():
            if value is None:
                continue
            if hasattr(row, key):
                setattr(row, key, value)

        self._collections.update(row)
        self._db.commit()
        self._db.refresh(row)
        return _ref_from_orm(row)

    def delete(
        self,
        collection_id: int,
        *,
        user: User,
        scope: AppScope | None = None,
    ) -> bool:
        if not self._enabled():
            return False

        row = self._collections.get(collection_id)
        if row is None or not self._can_write(row, user, scope):
            return False

        self._collections.delete(row)
        self._db.commit()
        return True

    def add_recipes(
        self,
        collection_id: int,
        recipe_ids: Iterable[int],
        *,
        user: User,
        scope: AppScope | None = None,
    ) -> int:
        if not self._enabled():
            return 0

        row = self._collections.get(collection_id)
        if row is None or row.is_dynamic or not self._can_write(row, user, scope):
            return 0

        added = 0
        position = len(self._links.list_for_collection(collection_id))
        for recipe_id in recipe_ids:
            if self._links.get_link(collection_id, recipe_id) is not None:
                continue
            self._links.add(
                CollectionRecipe(
                    collection_id=collection_id,
                    recipe_id=recipe_id,
                    position=position,
                    added_by_user_id=user.id,
                )
            )
            position += 1
            added += 1

        self._db.commit()
        return added

    def remove_recipe(
        self,
        collection_id: int,
        recipe_id: int,
        *,
        user: User,
        scope: AppScope | None = None,
    ) -> bool:
        if not self._enabled():
            return False

        row = self._collections.get(collection_id)
        if row is None or row.is_dynamic or not self._can_write(row, user, scope):
            return False

        ok = self._links.delete_by_ids(collection_id, recipe_id)
        if ok:
            self._db.commit()
        return ok
