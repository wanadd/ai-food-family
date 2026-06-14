"use client";

import Link from "next/link";

import { RecipeImage2026 } from "@/components/recipes-2026/RecipeImage2026";
import { cn } from "@/lib/planam/cn";
import {
  categoryLabel,
  mealLabel,
} from "@/lib/recipes/labels";
import { recipeCardHeading } from "@/lib/recipes/card-title";
import { cardKcalBadge } from "@/lib/recipes/nutrition";
import type { RecipeSummary } from "@/lib/recipes/types";

type RecipeGridCard2026Props = {
  recipe: RecipeSummary;
  href: string;
  onToggleFavorite?: () => void;
  togglingFavorite?: boolean;
  replaceMode?: boolean;
  isCurrentRecipe?: boolean;
  onReplace?: () => void;
  replacing?: boolean;
  onCardOpen?: () => void;
};

export function RecipeGridCard2026({
  recipe,
  href,
  onToggleFavorite,
  togglingFavorite = false,
  replaceMode = false,
  isCurrentRecipe = false,
  onReplace,
  replacing = false,
  onCardOpen,
}: RecipeGridCard2026Props) {
  const time = recipe.prep_time_minutes ?? recipe.cooking_time_minutes;
  const heading = recipeCardHeading(recipe);
  const kcal = cardKcalBadge(recipe);
  const meal = mealLabel(recipe.meal_type);
  const category = categoryLabel(recipe.category);

  return (
    <article className="flex h-full flex-col overflow-hidden rounded-card border border-pa-border bg-pa-surface shadow-soft transition active:scale-[0.98] dark:shadow-none">
      <Link href={href} className="flex flex-1 flex-col" onClick={() => onCardOpen?.()}>
        <div className="relative">
          <RecipeImage2026
            imageSource={recipe}
            alt={heading}
            variant="grid"
            mealType={recipe.meal_type}
          />
          {onToggleFavorite && !replaceMode ? (
            <button
              type="button"
              disabled={togglingFavorite}
              aria-label={recipe.is_favorited ? "Убрать из избранного" : "В избранное"}
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                onToggleFavorite();
              }}
              className={cn(
                "absolute right-2 top-2 flex size-9 items-center justify-center rounded-full",
                "bg-black/35 text-lg backdrop-blur-sm transition hover:bg-black/50",
                recipe.is_favorited ? "text-amber-300" : "text-white",
              )}
            >
              {recipe.is_favorited ? "★" : "☆"}
            </button>
          ) : null}
        </div>
        <div className="flex flex-1 flex-col p-3">
          <h3 className="pa26-card-title line-clamp-3 min-h-[3.25rem] leading-snug">
            {heading}
          </h3>
          <p className="pa26-caption mt-1 text-pa-muted">
            {time ? `${time} мин` : ""}
            {time && kcal ? " · " : ""}
            {kcal?.text ?? ""}
            {kcal?.approximate ? (
              <span className="ml-1 text-pa-muted/70">примерно</span>
            ) : null}
          </p>
          <div className="mt-2 flex min-h-[1.25rem] flex-wrap gap-1">
            {meal ? (
              <span className="rounded-pill bg-sage-50 px-2 py-0.5 pa26-micro font-semibold text-sage-700 dark:bg-sage-700/30 dark:text-sage-300">
                {meal}
              </span>
            ) : null}
            {category ? (
              <span className="rounded-pill bg-cream-deep px-2 py-0.5 pa26-micro text-pa-muted dark:bg-graphite-700/40">
                {category}
              </span>
            ) : null}
          </div>
        </div>
      </Link>
      {replaceMode ? (
        <div className="border-t border-pa-border px-3 py-2">
          <button
            type="button"
            disabled={isCurrentRecipe || replacing}
            onClick={(e) => {
              e.preventDefault();
              onReplace?.();
            }}
            className={cn(
              "w-full rounded-control py-2 pa26-micro font-semibold",
              isCurrentRecipe
                ? "text-pa-muted"
                : "bg-sage-500 text-white dark:bg-sage-400",
            )}
          >
            {isCurrentRecipe ? "Уже выбрано" : replacing ? "Замена…" : "Заменить"}
          </button>
        </div>
      ) : null}
    </article>
  );
}
