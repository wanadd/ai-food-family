"use client";

import { useEffect, useMemo, useState } from "react";

import { BottomSheet2026 } from "@/components/planam-2026/ui/BottomSheet2026";
import { Button2026 } from "@/components/planam-2026/ui/Button2026";
import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { useTelegram } from "@/components/TelegramProvider";
import { invalidate as invalidateCache } from "@/lib/cache/session-cache";
import { mealLabel } from "@/lib/recipes/labels";
import { addRecipeToMenu } from "@/lib/recipes/analysis-api";
import type { RecipeSummary } from "@/lib/recipes/types";
import { cn } from "@/lib/planam/cn";

type SheetMode = "add" | "replace";

type MenuSlotSheet2026Props = {
  open: boolean;
  recipe: RecipeSummary;
  mode: SheetMode;
  onClose: () => void;
  onSuccess?: () => void;
  onError?: (message: string) => void;
};

const MEAL_TYPES = ["breakfast", "lunch", "dinner", "snack"] as const;

function dateOptions(count = 7): { value: string; label: string }[] {
  const options: { value: string; label: string }[] = [];
  const today = new Date();
  for (let offset = 0; offset < count; offset += 1) {
    const d = new Date(today);
    d.setDate(today.getDate() + offset);
    const value = d.toISOString().slice(0, 10);
    const label =
      offset === 0
        ? "Сегодня"
        : offset === 1
          ? "Завтра"
          : d.toLocaleDateString("ru-RU", {
              weekday: "short",
              day: "numeric",
              month: "short",
            });
    options.push({ value, label });
  }
  return options;
}

export function MenuSlotSheet2026({
  open,
  recipe,
  mode,
  onClose,
  onSuccess,
  onError,
}: MenuSlotSheet2026Props) {
  const { initData } = useTelegram();
  const { mode: appMode } = useAppMode();
  const dates = useMemo(() => dateOptions(), []);
  const [planDate, setPlanDate] = useState(dates[0]?.value ?? "");
  const [mealType, setMealType] = useState<string>(
    recipe.meal_type && MEAL_TYPES.includes(recipe.meal_type as (typeof MEAL_TYPES)[number])
      ? recipe.meal_type
      : "dinner",
  );
  const [servings, setServings] = useState(recipe.servings || 2);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) {
      return;
    }
    setPlanDate(dates[0]?.value ?? "");
    setMealType(
      recipe.meal_type && MEAL_TYPES.includes(recipe.meal_type as (typeof MEAL_TYPES)[number])
        ? recipe.meal_type
        : "dinner",
    );
    setServings(recipe.servings || 2);
    setError(null);
  }, [open, dates, recipe.meal_type, recipe.servings]);

  const title = mode === "add" ? "Добавить в меню" : "Заменить блюдо в плане";

  async function handleSubmit() {
    if (!initData) {
      const message = "Войдите в приложение, чтобы добавить рецепт в меню";
      setError(message);
      onError?.(message);
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await addRecipeToMenu(initData, appMode, recipe.id, {
        date: planDate,
        meal_type: mealType,
        servings,
      });
      invalidateCache("selected-menu");
      invalidateCache("menu-overview");
      invalidateCache("shopping-list");
      onSuccess?.();
      onClose();
    } catch {
      const message = "Не удалось добавить рецепт в меню. Попробуйте ещё раз.";
      setError(message);
      onError?.(message);
    } finally {
      setBusy(false);
    }
  }

  const footer = (
    <Button2026
      variant="primary"
      className="w-full"
      onClick={() => void handleSubmit()}
      loading={busy}
    >
      Добавить в меню
    </Button2026>
  );

  return (
    <BottomSheet2026 open={open} title={title} onClose={onClose} footer={footer}>
      <div className="space-y-4">
        <p className="pa26-body">
          <strong>{recipe.display_title ?? recipe.title}</strong>
        </p>

        <div className="space-y-2">
          <p className="pa26-caption text-pa-muted">Дата</p>
          <div className="flex flex-wrap gap-2">
            {dates.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => setPlanDate(option.value)}
                className={cn(
                  "rounded-pill px-3 py-1.5 pa26-micro font-semibold",
                  planDate === option.value
                    ? "bg-sage-500 text-white dark:bg-sage-400"
                    : "border border-pa-border bg-pa-surface text-pa-muted",
                )}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <p className="pa26-caption text-pa-muted">Приём пищи</p>
          <div className="grid grid-cols-2 gap-2">
            {MEAL_TYPES.map((type) => (
              <button
                key={type}
                type="button"
                onClick={() => setMealType(type)}
                className={cn(
                  "rounded-card border px-3 py-2.5 text-left pa26-micro font-semibold",
                  mealType === type
                    ? "border-sage-500 bg-sage-50 text-sage-800 dark:border-sage-400 dark:bg-sage-700/30 dark:text-sage-200"
                    : "border-pa-border bg-pa-surface text-pa-muted",
                )}
              >
                {mealLabel(type)}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <label className="pa26-caption text-pa-muted" htmlFor="menu-servings">
            Порций
          </label>
          <input
            id="menu-servings"
            type="number"
            min={1}
            max={12}
            value={servings}
            onChange={(e) => setServings(Math.max(1, Number(e.target.value) || 1))}
            className="w-full rounded-card border border-pa-border bg-pa-surface px-3 py-2.5 pa26-body"
          />
        </div>

        {error ? <p className="pa26-caption text-pa-error">{error}</p> : null}
      </div>
    </BottomSheet2026>
  );
}
