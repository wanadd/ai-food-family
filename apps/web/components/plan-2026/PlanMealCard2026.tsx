"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { RecipeImage2026 } from "@/components/recipes-2026/RecipeImage2026";
import { Button2026 } from "@/components/planam-2026/ui/Button2026";
import { useToast } from "@/components/ui/ToastProvider";
import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { useTelegram } from "@/components/TelegramProvider";
import { addMealIngredientsToShopping } from "@/lib/plan/add-to-shopping";
import type { PlanTodayMeal } from "@/lib/plan/plan-today";
import { mealTypeLabel } from "@/lib/plan/plan-today";
import { recipeDetailPath } from "@/lib/plan/plan-paths";
import { cn } from "@/lib/planam/cn";

type PlanMealCard2026Props = {
  item: PlanTodayMeal;
  onCook?: () => void;
  onReplace?: () => void;
};

export function PlanMealCard2026({
  item,
  onCook,
  onReplace,
}: PlanMealCard2026Props) {
  const router = useRouter();
  const { initData } = useTelegram();
  const { mode } = useAppMode();
  const { showToast } = useToast();
  const [shoppingBusy, setShoppingBusy] = useState(false);

  const { meal, imageUrl, statusLabel, statusCode } = item;
  const metaParts: string[] = [];
  if (meal.prep_time_minutes > 0) {
    metaParts.push(`${meal.prep_time_minutes} мин`);
  }
  if (meal.calories_estimate != null && meal.calories_estimate > 0) {
    metaParts.push(`${Math.round(meal.calories_estimate)} ккал`);
  }

  async function handleShopping() {
    if (!initData) {
      return;
    }
    setShoppingBusy(true);
    try {
      const result = await addMealIngredientsToShopping(initData, mode, meal);
      if (result.ok) {
        showToast(`✓ ${result.message}`);
      } else {
        showToast(result.message);
      }
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Не удалось добавить");
    } finally {
      setShoppingBusy(false);
    }
  }

  return (
    <article className="overflow-hidden rounded-card border border-pa-border bg-pa-surface shadow-soft dark:shadow-none">
      <RecipeImage2026
        imageUrl={imageUrl}
        alt={meal.name}
        variant="hero"
        mealType={meal.meal_type}
        className="max-h-[180px] rounded-none"
      />
      <div className="p-4">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="pa26-micro text-pa-muted">{mealTypeLabel(meal.meal_type)}</p>
            <h3 className="pa26-card-title mt-0.5">{meal.name}</h3>
            {metaParts.length ? (
              <p className="pa26-caption mt-1 text-pa-muted">{metaParts.join(" · ")}</p>
            ) : null}
          </div>
          <span
            className={cn(
              "shrink-0 rounded-pill px-2.5 py-1 pa26-micro font-semibold",
              statusCode
                ? "bg-sage-50 text-sage-700 dark:bg-sage-700/30 dark:text-sage-300"
                : "bg-cream-deep text-pa-muted dark:bg-graphite-700/40",
            )}
          >
            {statusLabel}
          </span>
        </div>

        <div className="mt-3 flex flex-wrap gap-2">
          <Button2026 variant="primary" className="flex-1 min-w-[100px]" onClick={onCook}>
            Приготовил
          </Button2026>
          <Button2026 variant="secondary" onClick={onReplace}>
            Заменить
          </Button2026>
          {meal.recipe_id ? (
            <Button2026
              variant="ghost"
              onClick={() => router.push(recipeDetailPath(meal.recipe_id!))}
            >
              Рецепт
            </Button2026>
          ) : null}
        </div>
        <Button2026
          variant="ghost"
          className="mt-2 w-full"
          loading={shoppingBusy}
          onClick={() => void handleShopping()}
        >
          В покупки
        </Button2026>
      </div>
    </article>
  );
}
