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
    <article className="rounded-2xl border border-stone-200 bg-white p-4 shadow-sm transition hover:border-emerald-200">
      <div className="flex items-start justify-between gap-2">
        <button type="button" onClick={onOpen} className="min-w-0 flex-1 text-left">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-semibold text-stone-900">{recipe.title}</h3>
            {recipe.fit_level ? (
              <span
                className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${FIT_BADGE_STYLES[recipe.fit_level as RecipeFitLevel]}`}
              >
                {FIT_BADGE_LABELS[recipe.fit_level as RecipeFitLevel]}
              </span>
            ) : null}
          </div>
          <p className="mt-1 line-clamp-2 text-sm text-stone-500">
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
          className="shrink-0 text-xl disabled:opacity-50"
        >
          {recipe.is_favorited ? "★" : "☆"}
        </button>
      </div>

      <button type="button" onClick={onOpen} className="mt-3 w-full text-left">
        <div className="flex flex-wrap gap-2">
          <span className="rounded-full bg-violet-100 px-2.5 py-1 text-xs font-semibold text-violet-800">
            {mealLabel(recipe.meal_type)}
          </span>
          <span className="rounded-full bg-stone-100 px-2.5 py-1 text-xs font-medium text-stone-600">
            {categoryLabel(recipe.category)}
          </span>
          <span className="rounded-full bg-amber-50 px-2.5 py-1 text-xs font-medium text-amber-800">
            {recipe.prep_time_minutes} мин
          </span>
          <span className="rounded-full bg-stone-100 px-2.5 py-1 text-xs font-medium text-stone-500">
            {difficultyLabel(recipe.difficulty)}
          </span>
        </div>
      </button>
    </article>
  );
}
