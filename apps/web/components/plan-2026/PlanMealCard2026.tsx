"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { RecipeImage2026 } from "@/components/recipes-2026/RecipeImage2026";
import { buildReplaceCatalogUrl } from "@/lib/menu/replace-slot";
import { withReturnTo } from "@/lib/navigation/return-to";
import { recipeDetailPath } from "@/lib/plan/plan-paths";
import type { PlanTodayMeal } from "@/lib/plan/plan-today";
import { mealTypeLabel } from "@/lib/plan/plan-today";
import { cn } from "@/lib/planam/cn";

type PlanMealCard2026Props = {
  item: PlanTodayMeal;
  highlighted?: boolean;
  onCook?: () => void;
  onReplace?: () => void;
  onRemove?: () => void;
};

export function PlanMealCard2026({
  item,
  highlighted = false,
  onCook,
  onReplace,
  onRemove,
}: PlanMealCard2026Props) {
  const router = useRouter();
  const [removeOpen, setRemoveOpen] = useState(false);

  const { meal, imageUrl, statusLabel } = item;
  const metaParts: string[] = [];
  if (meal.prep_time_minutes > 0) {
    metaParts.push(`${meal.prep_time_minutes} мин`);
  }
  if (meal.calories_estimate != null && meal.calories_estimate > 0) {
    metaParts.push(`${Math.round(meal.calories_estimate)} ккал`);
  }

  function handleReplace() {
    if (onReplace) {
      onReplace();
      return;
    }
    if (item.slotId) {
      router.push(
        buildReplaceCatalogUrl(
          item.slotId,
          item.meal.recipe_id ?? undefined,
          "/plan/today",
        ),
      );
    }
  }

  function handleOpen() {
    if (meal.recipe_id) {
      router.push(withReturnTo(recipeDetailPath(meal.recipe_id), "/plan/today"));
      return;
    }
    onCook?.();
  }

  function handleRemove() {
    if (!onRemove) {
      return;
    }
    if (!removeOpen) {
      setRemoveOpen(true);
      return;
    }
    onRemove();
    setRemoveOpen(false);
  }

  return (
    <article
      id={`meal-card-${item.meal.meal_type}`}
      data-meal-type={item.meal.meal_type}
      data-recipe-id={item.meal.recipe_id ?? undefined}
      data-slot-id={item.slotId ?? undefined}
      className={cn(
        "overflow-hidden rounded-card border bg-pa-surface shadow-soft dark:shadow-none",
        highlighted
          ? "border-pa-brand ring-2 ring-pa-brand/30"
          : "border-pa-border",
      )}
    >
      <div className="flex w-full items-center gap-3 p-3">
        <button
          type="button"
          onClick={handleOpen}
          className="flex min-w-0 flex-1 items-center gap-3 text-left transition hover:opacity-90"
        >
          <div className="relative size-14 shrink-0 overflow-hidden rounded-control">
            <RecipeImage2026
              imageUrl={imageUrl}
              alt={meal.name}
              variant="thumb"
              mealType={meal.meal_type}
              className="size-full"
            />
          </div>
          <div className="min-w-0 flex-1">
            <p className="pa26-micro text-pa-muted">{mealTypeLabel(meal.meal_type)}</p>
            <h3 className="pa26-card-title line-clamp-2 leading-snug">{meal.name}</h3>
            {metaParts.length ? (
              <p className="pa26-micro mt-0.5 text-pa-muted">{metaParts.join(" · ")}</p>
            ) : null}
            {statusLabel ? (
              <p className="pa26-micro mt-0.5 font-medium text-sage-700 dark:text-sage-300">
                {statusLabel}
              </p>
            ) : null}
          </div>
        </button>
        <button
          type="button"
          onClick={handleReplace}
          className="flex size-9 shrink-0 items-center justify-center rounded-full border border-pa-border bg-pa-elevated pa26-card-title text-sage-700 transition hover:bg-sage-50 dark:text-sage-300 dark:hover:bg-sage-800/40"
          aria-label="Заменить блюдо"
        >
          +
        </button>
      </div>

      {onRemove ? (
        <div className="border-t border-pa-border px-3 pb-2 pt-1 text-center">
          <button
            type="button"
            className={cn(
              "pa26-micro text-pa-muted underline-offset-2 hover:underline",
              removeOpen && "text-pa-error",
            )}
            onClick={handleRemove}
          >
            {removeOpen ? "Подтвердить удаление" : "Удалить из меню"}
          </button>
        </div>
      ) : null}
    </article>
  );
}
