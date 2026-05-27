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

from app.models.user import User
from app.services.app_scope import AppScope


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
    """Read/write façade for collections.

    Sprint 1 status:

      - Read methods return empty results (no table exists yet).
      - Write methods raise ``NotImplementedError`` so that any caller
        wired in by mistake fails loudly rather than silently corrupting
        data.

    The ``CollectionService`` is the only entry point future commits and
    Sprint 2 routes should depend on.
    """

    _WRITE_NOT_AVAILABLE_MSG = (
        "Collection write API is reserved for Sprint 2 — gated by the "
        "`recipe_collections` feature flag (see commit 8)."
    )

    def __init__(self, db: Session) -> None:
        self._db = db

    # ------------------------------------------------------------------ read

    def list_visible(
        self, user: User, scope: AppScope | None = None
    ) -> list[CollectionRef]:
        """List collections visible to the user in the given scope.

        Sprint 2 will query ``recipe_collections`` with visibility rules:
        ``system`` + the user's own ``personal`` + the active family's
        ``family`` collections.
        """

        _ = (user, scope)
        return []

    def get(
        self,
        collection_id: int,
        *,
        user: User,
        scope: AppScope | None = None,
    ) -> CollectionDetail | None:
        _ = (collection_id, user, scope)
        return None

    def resolve_dynamic(
        self,
        collection: CollectionRef,
        *,
        user: User,
        scope: AppScope | None = None,
    ) -> tuple[int, ...]:
        """Resolve the recipe set of a *dynamic* collection at read time.

        Used for collections whose membership is computed (e.g. the
        ``Из запасов`` system collection in
        ``docs/RECIPE_ENGINE_V1.md`` § 2.17). Stub returns empty until
        the from-pantry pipeline lands in Sprint 2.
        """

        _ = (collection, user, scope)
        return ()

    # ----------------------------------------------------------------- write

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
        _ = (name, visibility, user, scope, description, emoji, color)
        raise NotImplementedError(self._WRITE_NOT_AVAILABLE_MSG)

    def update(
        self,
        collection_id: int,
        *,
        user: User,
        scope: AppScope | None = None,
        **changes: object,
    ) -> CollectionRef | None:
        _ = (collection_id, user, scope, changes)
        raise NotImplementedError(self._WRITE_NOT_AVAILABLE_MSG)

    def delete(
        self,
        collection_id: int,
        *,
        user: User,
        scope: AppScope | None = None,
    ) -> bool:
        _ = (collection_id, user, scope)
        raise NotImplementedError(self._WRITE_NOT_AVAILABLE_MSG)

    def add_recipes(
        self,
        collection_id: int,
        recipe_ids: Iterable[int],
        *,
        user: User,
        scope: AppScope | None = None,
    ) -> int:
        _ = (collection_id, list(recipe_ids), user, scope)
        raise NotImplementedError(self._WRITE_NOT_AVAILABLE_MSG)

    def remove_recipe(
        self,
        collection_id: int,
        recipe_id: int,
        *,
        user: User,
        scope: AppScope | None = None,
    ) -> bool:
        _ = (collection_id, recipe_id, user, scope)
        raise NotImplementedError(self._WRITE_NOT_AVAILABLE_MSG)
