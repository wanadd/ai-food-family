"""Recipe Engine entity repositories (SQLAlchemy CRUD)."""

from app.services.recipes.repositories.collections import CollectionRecipeRepository
from app.services.recipes.repositories.collections import RecipeCollectionRepository
from app.services.recipes.repositories.explanations import RecipeExplanationRepository
from app.services.recipes.repositories.history import RecipeHistoryRepository
from app.services.recipes.repositories.preferences import FamilyRecipePreferenceRepository
from app.services.recipes.repositories.scenarios import RecipeScenarioRepository

__all__ = [
    "CollectionRecipeRepository",
    "FamilyRecipePreferenceRepository",
    "RecipeCollectionRepository",
    "RecipeExplanationRepository",
    "RecipeHistoryRepository",
    "RecipeScenarioRepository",
]
