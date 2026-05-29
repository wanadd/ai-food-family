"use client";

import { RecipeCard } from "@/components/recipes/RecipeCard";
import type { RecipeSummary } from "@/lib/recipes/types";

type RecipeResultsListProps = {
  recipes: RecipeSummary[];
  onOpen: (id: number) => void;
  onToggleFavorite: (id: number) => void;
  togglingId: number | null;
};

/** Простой список карточек рецептов (переиспользуется в Рецептах и Избранном). */
export function RecipeResultsList({
  recipes,
  onOpen,
  onToggleFavorite,
  togglingId,
}: RecipeResultsListProps) {
  return (
    <div className="space-y-3">
      {recipes.map((recipe) => (
        <RecipeCard
          key={recipe.id}
          recipe={recipe}
          onOpen={() => onOpen(recipe.id)}
          onToggleFavorite={() => onToggleFavorite(recipe.id)}
          togglingFavorite={togglingId === recipe.id}
        />
      ))}
    </div>
  );
}
