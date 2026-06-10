"""Internal types and extension points for the Recipe Engine.

These types are **not** the public DTO surface — those live in
``app.schemas.recipe``. They are domain-internal value types used to share
context across the catalog, search, scoring, explainability and
recommendation pipelines.

Subsequent Sprint 1 commits extend this module:

  - commit 2 — ``SearchFilters``, ``SearchResult``, ``RecipeSortOrder``
    (``RecipeSearchQuery`` / ``RecipeSearchResponse`` live in
    ``app.schemas.recipe_search`` as Pydantic models).
  - commit 3 — ``RecommendationReason``, ``ExplainabilityResult``
  - commit 4 — ``CollectionVisibility``, ``CollectionRef``
  - commit 5 — ``CookingEvent``, ``CookingStats``
  - commit 6 — ``FamilyPreferenceScore``, ``FamilyCompatibilityResult``
  - commit 7 — ``ScenarioCode``, ``ScenarioMatchResult``
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


@dataclass(frozen=True)
class RecipeListFilters:
    """Repository-level filter set for ``query_recipes``.

    The router/service layers translate public query parameters into this
    immutable record before handing it down to the repository.

    Kept intentionally narrow. Anything richer (sorting policy, scoring,
    pagination cursor, full-text relevance) belongs in ``SearchFilters``
    introduced in commit 2.
    """

    q: str | None = None
    meal_type: str | None = None
    category: str | None = None
    diet: str | None = None
    difficulty: str | None = None
    max_prep_time: int | None = None
    favorites_only: bool = False
    favorite_ids: frozenset[int] = field(default_factory=frozenset)
    for_children: bool = False
    for_sport: bool = False
    for_event: bool = False
    drinks_only: bool = False
    non_alcoholic: bool = False
    alcoholic_only: bool = False
    protein_only: bool = False
    smoothie_only: bool = False
    tea_coffee_only: bool = False
    include_legacy: bool = False
    limit: int | None = None
    offset: int = 0


class RecipeSortOrder(str, Enum):
    """Sort policy for future recipe search.

    In Sprint 2 we only scaffold the contract; current implementation
    still uses the legacy ordering inside ``catalog.list_recipes``.
    """

    title = "title"
    relevance = "relevance"
    popularity = "popularity"
    score = "score"
