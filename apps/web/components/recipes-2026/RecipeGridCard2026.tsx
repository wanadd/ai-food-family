"use client";

import Link from "next/link";

import { RecipeImage2026 } from "@/components/recipes-2026/RecipeImage2026";
import { cn } from "@/lib/planam/cn";
import {
  categoryLabel,
  difficultyLabel,
  mealLabel,
} from "@/lib/recipes/labels";
import type { RecipeSummary } from "@/lib/recipes/types";

type RecipeGridCard2026Props = {
  recipe: RecipeSummary;
  href: string;
  onToggleFavorite?: () => void;
  togglingFavorite?: boolean;
};

function formatKcal(recipe: RecipeSummary): string | null {
  if (recipe.calories_per_serving == null) {
    return null;
  }
  return `${Math.round(recipe.calories_per_serving)} ккал`;
}

export function RecipeGridCard2026({
  recipe,
  href,
  onToggleFavorite,
  togglingFavorite = false,
}: RecipeGridCard2026Props) {
  const time = recipe.prep_time_minutes ?? recipe.cooking_time_minutes;

  return (
    <article className="overflow-hidden rounded-card border border-pa-border bg-pa-surface shadow-soft transition active:scale-[0.98] dark:shadow-none">
      <Link href={href} className="block">
        <RecipeImage2026
          imageUrl={recipe.image_url}
          alt={recipe.title}
          variant="grid"
          mealType={recipe.meal_type}
        />
        <div className="p-3">
          <h3 className="pa26-card-title line-clamp-2">{recipe.title}</h3>
          <p className="pa26-caption mt-1 text-pa-muted">
            {time ? `${time} мин` : ""}
            {time && formatKcal(recipe) ? " · " : ""}
            {formatKcal(recipe) ?? ""}
          </p>
          <div className="mt-2 flex flex-wrap gap-1">
            <span className="rounded-pill bg-sage-50 px-2 py-0.5 pa26-micro font-semibold text-sage-700 dark:bg-sage-700/30 dark:text-sage-300">
              {mealLabel(recipe.meal_type)}
            </span>
            {recipe.category ? (
              <span className="rounded-pill bg-cream-deep px-2 py-0.5 pa26-micro text-pa-muted dark:bg-graphite-700/40">
                {categoryLabel(recipe.category)}
              </span>
            ) : null}
          </div>
        </div>
      </Link>
      {onToggleFavorite ? (
        <div className="border-t border-pa-border px-3 py-2">
          <button
            type="button"
            disabled={togglingFavorite}
            onClick={(e) => {
              e.preventDefault();
              onToggleFavorite();
            }}
            className={cn(
              "pa26-micro font-semibold",
              recipe.is_favorited
                ? "text-sage-600 dark:text-sage-300"
                : "text-pa-muted",
            )}
          >
            {recipe.is_favorited ? "★ В избранном" : "☆ В избранное"}
          </button>
        </div>
      ) : null}
    </article>
  );
}
