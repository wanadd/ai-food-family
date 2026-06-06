#!/usr/bin/env python3
"""Single source of truth for resolving a recipe by TITLE.

The recipe image pipeline must NEVER trust the ``recipe_id`` carried inside a
pilot JSON file — that value is only a batch index (1..N) and collides with
archived ``manual`` recipes that hold those primary keys. The only reliable
key is the recipe title, scoped to active V1 catalog recipes:

    SELECT id FROM recipes
    WHERE source_type = 'v1_import'
      AND is_active = true
      AND lower(title) = lower(:title)

Ambiguous (>1) or missing (0) matches are hard errors, never a fallback to an
index or row position.
"""

from __future__ import annotations

from typing import Any

V1_SOURCE_TYPE = "v1_import"


class RecipeResolutionError(RuntimeError):
    """Raised when a title maps to zero or more than one active v1_import recipe."""


def _norm(value: Any) -> str:
    return str(value or "").strip().casefold()


def resolve_v1_recipe_id_by_title(session: Any, recipe_model: Any, title: str) -> int:
    """Return the id of the single active v1_import recipe matching ``title``.

    Unicode-correct, case-insensitive comparison (works on PostgreSQL and
    SQLite). Raises :class:`RecipeResolutionError` on 0 or >1 matches.
    """
    target = _norm(title)
    if not target:
        raise RecipeResolutionError("empty title — cannot resolve recipe")

    candidates = (
        session.query(recipe_model)
        .filter(recipe_model.source_type == V1_SOURCE_TYPE)
        .filter(recipe_model.is_active.is_(True))
        .all()
    )
    matches = [row for row in candidates if _norm(row.title) == target]

    if len(matches) > 1:
        ids = sorted(row.id for row in matches)
        raise RecipeResolutionError(
            f"ambiguous title {title!r}: {len(matches)} active v1_import matches ids={ids}"
        )
    if not matches:
        raise RecipeResolutionError(
            f"no active v1_import recipe found for title {title!r}"
        )
    return matches[0].id
