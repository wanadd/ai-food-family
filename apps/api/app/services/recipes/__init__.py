"""Recipe Engine — service package facade.

This package replaces the legacy ``app.services.recipes`` single-file module
without changing its public surface. External callers continue to write::

    from app.services.recipes import seed_recipes_if_empty, list_recipes, ...

Internally the code is split into a layered architecture per
``docs/RECIPE_ENGINE_V1.md`` § 2.5:

  - ``repository``        : SQLAlchemy access (no domain logic)
  - ``mapper``            : ORM → DTO conversion
  - ``catalog``           : list / get / filters / seed
  - ``authoring``         : create / update / favorite / add-to-shopping
  - ``recommendations``   : simple heuristic recommendations (current)
  - ``types``             : internal types & extension points

Extension points (filled in by subsequent Sprint 1 commits):

  - ``search``         (commit 2)
  - ``explainability`` (commit 3)
  - ``collections``    (commit 4)
  - ``cooked``         (commit 5) — cooking history
  - ``family``         (commit 6) — family preference scoring
  - ``scenarios``      (commit 7)

Lower-level helpers (``recipe_storage``, ``recipe_analysis``) remain in their
existing modules — folding them into the package is a Sprint 2 candidate.
"""

from app.services.recipes.authoring import (
    add_recipe_to_shopping,
    create_recipe,
    toggle_favorite,
    update_recipe,
)
from app.services.recipes.catalog import (
    FILTER_LABELS,
    get_filters,
    get_recipe,
    get_recipe_model,
    list_recipes,
    seed_recipes_if_empty,
)
from app.services.recipes.recommendations import get_recommendations
from app.services.recipes.search import SearchService
from app.services.recipes.explainability import (
    ExplainabilityResult,
    ExplainabilityService,
    RecommendationReason,
    RecommendationReasonEntry,
)
from app.services.recipes.cooking_history import (
    CookingEvent,
    CookingHistoryService,
    CookingStats,
    HistoryTypes,
)

__all__ = [
    "FILTER_LABELS",
    "CookingEvent",
    "CookingHistoryService",
    "CookingStats",
    "HistoryTypes",
    "ExplainabilityResult",
    "ExplainabilityService",
    "RecommendationReason",
    "RecommendationReasonEntry",
    "add_recipe_to_shopping",
    "create_recipe",
    "get_filters",
    "get_recipe",
    "get_recipe_model",
    "get_recommendations",
    "list_recipes",
    "seed_recipes_if_empty",
    "toggle_favorite",
    "update_recipe",
    "SearchService",
]
