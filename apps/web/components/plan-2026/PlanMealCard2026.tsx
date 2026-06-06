"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { RecipeImage2026 } from "@/components/recipes-2026/RecipeImage2026";
import { Button2026 } from "@/components/planam-2026/ui/Button2026";
import { buildReplaceCatalogUrl } from "@/lib/menu/replace-slot";
import { withReturnTo } from "@/lib/navigation/return-to";
import { recipeDetailPath } from "@/lib/plan/plan-paths";
import type { PlanTodayMeal } from "@/lib/plan/plan-today";
import { mealTypeLabel } from "@/lib/plan/plan-today";
import { cn } from "@/lib/planam/cn";

type PlanMealCard2026Props = {
  item: PlanTodayMeal;
  onCook?: () => void;
  onReplace?: () => void;
  onRemove?: () => void;
};

export function PlanMealCard2026({
  item,
  onCook,
  onReplace,
  onRemove,
}: PlanMealCard2026Props) {
  const router = useRouter();
  const [removeOpen, setRemoveOpen] = useState(false);

  const { meal, imageUrl, statusLabel, statusCode } = item;
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

  function handleRecipe() {
    if (!meal.recipe_id) {
      return;
    }
    router.push(withReturnTo(recipeDetailPath(meal.recipe_id), "/plan/today"));
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
    <article className="overflow-hidden rounded-card border border-pa-border bg-pa-surface shadow-soft dark:shadow-none">
      <div className="relative min-h-[160px] w-full">
        <RecipeImage2026
          imageUrl={imageUrl}
          alt={meal.name}
          variant="hero"
          mealType={meal.meal_type}
          className="absolute inset-0 max-h-none h-full rounded-none"
        />
        <div
          className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent"
          aria-hidden
        />
        <div className="absolute inset-x-0 bottom-0 p-3 text-white">
          <p className="pa26-micro text-white/80">{mealTypeLabel(meal.meal_type)}</p>
          <h3 className="pa26-card-title mt-0.5 text-white">{meal.name}</h3>
          {metaParts.length ? (
            <p className="pa26-caption mt-0.5 text-white/85">{metaParts.join(" · ")}</p>
          ) : null}
        </div>
        <span
          className={cn(
            "absolute right-3 top-3 rounded-pill px-2.5 py-1 pa26-micro font-semibold",
            statusCode
              ? "bg-white/90 text-sage-700"
              : "bg-black/40 text-white",
          )}
        >
          {statusLabel}
        </span>
      </div>

      <div className="flex gap-2 p-3">
        <Button2026 variant="primary" className="flex-1" onClick={onCook}>
          Приготовить
        </Button2026>
        {meal.recipe_id ? (
          <Button2026 variant="secondary" onClick={handleRecipe}>
            Рецепт
          </Button2026>
        ) : null}
        <Button2026 variant="secondary" onClick={handleReplace}>
          Заменить
        </Button2026>
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
