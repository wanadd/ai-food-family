"use client";

import {
  categoryLabel,
  difficultyLabel,
  hasCategoryLabel,
  hasMealLabel,
  mealLabel,
} from "@/lib/recipes/labels";
import { recipeCardHeading } from "@/lib/recipes/card-title";
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

function hasNutrition(recipe: RecipeSummary): boolean {
  return [
    recipe.calories_per_serving,
    recipe.protein_g,
    recipe.fat_g,
    recipe.carbs_g,
  ].some((value) => value != null);
}

export function RecipeCard({
  recipe,
  onOpen,
  onToggleFavorite,
  togglingFavorite,
}: RecipeCardProps) {
  const heading = recipeCardHeading(recipe);
  const meal = mealLabel(recipe.meal_type);
  const category = categoryLabel(recipe.category);

  return (
    <article className="pa-card p-4 transition hover:border-sage-200">
      <div className="flex items-start justify-between gap-2">
        <button type="button" onClick={onOpen} className="min-w-0 flex-1 text-left">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="line-clamp-2 min-h-[2.75rem] font-semibold leading-snug text-graphite-900">
              {heading}
            </h3>
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
          {meal ? (
            <span className="rounded-pill bg-sage-50 px-2.5 py-1 text-xs font-semibold text-sage-700">
              {meal}
            </span>
          ) : null}
          {category ? (
            <span className="rounded-pill bg-cream-deep px-2.5 py-1 text-xs font-medium text-graphite-500">
              {category}
            </span>
          ) : null}
          <span className="rounded-pill bg-warm/10 px-2.5 py-1 text-xs font-medium text-graphite-700">
            {recipe.prep_time_minutes} мин
          </span>
          <span className="rounded-pill bg-cream-deep px-2.5 py-1 text-xs font-medium text-graphite-400">
            {difficultyLabel(recipe.difficulty)}
          </span>
          {hasNutrition(recipe) ? (
            <span className="rounded-pill bg-cream-deep px-2.5 py-1 text-xs font-medium text-graphite-600">
              {recipe.calories_per_serving != null
                ? `${Math.round(recipe.calories_per_serving)} ккал`
                : "ккал —"}{" "}
              · Б/Ж/У{" "}
              {recipe.protein_g != null ? Math.round(recipe.protein_g) : "—"}/
              {recipe.fat_g != null ? Math.round(recipe.fat_g) : "—"}/
              {recipe.carbs_g != null ? Math.round(recipe.carbs_g) : "—"}
            </span>
          ) : null}
        </div>
      </button>
    </article>
  );
}
