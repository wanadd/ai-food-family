"""Collection-facing DTOs for the Recipe Engine.

Pydantic mirrors of the dataclasses defined in
``app.services.recipes.collections``. Not wired to any router in Sprint 1.

Sprint 2 endpoints from ``docs/RECIPE_ENGINE_V1.md`` § 2.6 will accept
``CollectionCreateRequest`` / ``CollectionUpdateRequest`` /
``AddRecipesToCollectionRequest`` and return ``CollectionResponse`` /
``CollectionDetailResponse`` without modification.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


VisibilityLiteral = Literal["system", "personal", "family"]


class CollectionResponse(BaseModel):
    """Slim collection card for list views."""

    id: int
    name: str
    visibility: VisibilityLiteral
    description: str = ""
    emoji: str | None = None
    color: str | None = None
    is_pinned: bool = False
    is_dynamic: bool = False
    recipes_count: int = 0
    owner_user_id: int | None = None
    owner_family_id: int | None = None


class CollectionDetailResponse(BaseModel):
    """Full collection detail. Recipe payloads are added in Sprint 2."""

    collection: CollectionResponse
    recipe_ids: list[int] = Field(default_factory=list)


class CollectionCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    visibility: VisibilityLiteral = "personal"
    description: str = Field(default="", max_length=500)
    emoji: str | None = Field(default=None, max_length=8)
    color: str | None = Field(default=None, max_length=16)


class CollectionUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    emoji: str | None = Field(default=None, max_length=8)
    color: str | None = Field(default=None, max_length=16)
    is_pinned: bool | None = None


class AddRecipesToCollectionRequest(BaseModel):
    recipe_ids: list[int] = Field(min_length=1, max_length=200)
