"use client";

import {
  categoryLabel,
  difficultyLabel,
  mealLabel,
} from "@/lib/recipes/labels";
import {
  FIT_BADGE_LABELS,
  FIT_BADGE_STYLES,
  type RecipeFitLevel,
} from "@/lib/recipes/fit-labels";
import type { RecipeSummary } from "@/lib/recipes/types";

type RecipeCardProps = {
  recipe: RecipeSummary;
  onOpen: () => void;
  onToggleFavorite: () => void;
  togglingFavorite: boolean;
};

export function RecipeCard({
  recipe,
  onOpen,
  onToggleFavorite,
  togglingFavorite,
}: RecipeCardProps) {
  return (
    <article className="pa-card p-4 transition hover:border-sage-200">
      <div className="flex items-start justify-between gap-2">
        <button type="button" onClick={onOpen} className="min-w-0 flex-1 text-left">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-semibold text-graphite-900">{recipe.title}</h3>
            {recipe.fit_level ? (
              <span
                className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${FIT_BADGE_STYLES[recipe.fit_level as RecipeFitLevel]}`}
              >
                {FIT_BADGE_LABELS[recipe.fit_level as RecipeFitLevel]}
              </span>
            ) : null}
          </div>
          <p className="mt-1 line-clamp-2 text-sm text-graphite-500">
            {recipe.description}
          </p>
        </button>
        <button
          type="button"
          aria-label={recipe.is_favorited ? "Убрать из избранного" : "В избранное"}
          disabled={togglingFavorite}
          onClick={(event) => {
            event.stopPropagation();
            onToggleFavorite();
          }}
          className={`shrink-0 text-xl disabled:opacity-50 ${
            recipe.is_favorited ? "text-sage-600" : "text-graphite-300"
          }`}
        >
          {recipe.is_favorited ? "★" : "☆"}
        </button>
      </div>

      <button type="button" onClick={onOpen} className="mt-3 w-full text-left">
        <div className="flex flex-wrap gap-2">
          <span className="rounded-pill bg-sage-50 px-2.5 py-1 text-xs font-semibold text-sage-700">
            {mealLabel(recipe.meal_type)}
          </span>
          <span className="rounded-pill bg-cream-deep px-2.5 py-1 text-xs font-medium text-graphite-500">
            {categoryLabel(recipe.category)}
          </span>
          <span className="rounded-pill bg-warm/10 px-2.5 py-1 text-xs font-medium text-graphite-700">
            {recipe.prep_time_minutes} мин
          </span>
          <span className="rounded-pill bg-cream-deep px-2.5 py-1 text-xs font-medium text-graphite-400">
            {difficultyLabel(recipe.difficulty)}
          </span>
        </div>
      </button>
    </article>
  );
}
