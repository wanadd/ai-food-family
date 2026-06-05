"use client";

import { useEffect, useState } from "react";

import { BottomSheet2026 } from "@/components/planam-2026/ui/BottomSheet2026";
import { Button2026 } from "@/components/planam-2026/ui/Button2026";
import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { useTelegram } from "@/components/TelegramProvider";
import { invalidate as invalidateCache } from "@/lib/cache/session-cache";
import { fetchSelectedMenu } from "@/lib/menu/api";
import { dateIsoForDayIndex, getMenuDays, mealsForDayIndex } from "@/lib/menu/menu-days";
import type { MenuVariant } from "@/lib/menu/types";
import { assignRecipeToMenuSlot } from "@/lib/recipes/menu-from-recipe";
import { mealLabel } from "@/lib/recipes/labels";
import type { RecipeSummary } from "@/lib/recipes/types";
import { cn } from "@/lib/planam/cn";

type SheetMode = "add" | "replace";

type MenuSlotSheet2026Props = {
  open: boolean;
  recipe: RecipeSummary;
  mode: SheetMode;
  onClose: () => void;
  onSuccess?: () => void;
};

type Step = "day" | "meal" | "confirm";

export function MenuSlotSheet2026({
  open,
  recipe,
  mode,
  onClose,
  onSuccess,
}: MenuSlotSheet2026Props) {
  const { initData } = useTelegram();
  const { mode: appMode } = useAppMode();
  const [step, setStep] = useState<Step>("day");
  const [menu, setMenu] = useState<MenuVariant | null>(null);
  const [loadingMenu, setLoadingMenu] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dayIndex, setDayIndex] = useState<number | null>(null);
  const [mealIndex, setMealIndex] = useState<number | null>(null);

  useEffect(() => {
    if (!open || !initData) {
      return;
    }
    setStep("day");
    setDayIndex(null);
    setMealIndex(null);
    setError(null);
    setLoadingMenu(true);
    fetchSelectedMenu(initData, appMode)
      .then((selected) => setMenu(selected?.menu ?? null))
      .catch(() => setMenu(null))
      .finally(() => setLoadingMenu(false));
  }, [open, initData, appMode]);

  const days = menu ? getMenuDays(menu) : [];
  const meals =
    menu && dayIndex != null ? mealsForDayIndex(menu, dayIndex) : [];

  const title =
    mode === "add" ? "Добавить в меню" : "Заменить блюдо в плане";

  async function handleConfirm() {
    if (!initData || !menu || dayIndex == null || mealIndex == null) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await assignRecipeToMenuSlot(
        initData,
        appMode,
        recipe,
        menu,
        dayIndex,
        mealIndex,
      );
      invalidateCache("selected-menu");
      invalidateCache("menu-overview");
      invalidateCache("shopping-list");
      onSuccess?.();
      onClose();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Не удалось обновить меню. Сначала создайте план.",
      );
    } finally {
      setBusy(false);
    }
  }

  const footer =
    step === "confirm" ? (
      <div className="flex gap-2">
        <Button2026 variant="ghost" className="flex-1" onClick={() => setStep("meal")}>
          Назад
        </Button2026>
        <Button2026
          variant="primary"
          className="flex-1"
          onClick={() => void handleConfirm()}
          loading={busy}
        >
          {mode === "add" ? "Добавить" : "Заменить"}
        </Button2026>
      </div>
    ) : null;

  return (
    <BottomSheet2026 open={open} title={title} onClose={onClose} footer={footer}>
      {loadingMenu ? (
        <p className="pa26-body text-pa-muted">Загружаем ваш план…</p>
      ) : !menu ? (
        <p className="pa26-body text-pa-muted">
          Сначала создайте меню на неделю — затем можно добавить «{recipe.title}».
        </p>
      ) : step === "day" ? (
        <div className="space-y-2">
          <p className="pa26-caption text-pa-muted">Выберите день</p>
          {days.map((day) => (
            <button
              key={day.day_index}
              type="button"
              onClick={() => {
                setDayIndex(day.day_index);
                setStep("meal");
              }}
              className="flex w-full items-center justify-between rounded-card border border-pa-border bg-pa-surface px-4 py-3 text-left transition hover:bg-sage-50 pa26-hover-row"
            >
              <span className="pa26-card-title">{day.label}</span>
              <span className="pa26-caption text-pa-muted">
                {day.date_iso ?? dateIsoForDayIndex(menu, day.day_index)}
              </span>
            </button>
          ))}
        </div>
      ) : step === "meal" ? (
        <div className="space-y-2">
          <p className="pa26-caption text-pa-muted">
            {mode === "replace" ? "Какое блюдо заменить?" : "Куда добавить?"}
          </p>
          {meals.length === 0 ? (
            <p className="pa26-body text-pa-muted">На этот день нет приёмов пищи в плане.</p>
          ) : (
            meals.map((meal, index) => (
              <button
                key={`${meal.meal_type}-${index}`}
                type="button"
                onClick={() => {
                  setMealIndex(index);
                  setStep("confirm");
                }}
                className="flex w-full flex-col rounded-card border border-pa-border bg-pa-surface px-4 py-3 text-left transition hover:bg-sage-50 pa26-hover-row"
              >
                <span className="pa26-micro text-pa-muted">
                  {mealLabel(meal.meal_type)}
                </span>
                <span className="pa26-card-title">{meal.name}</span>
              </button>
            ))
          )}
          <button
            type="button"
            className="pa26-caption font-semibold text-sage-700 dark:text-sage-300"
            onClick={() => setStep("day")}
          >
            ← Другой день
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          <p className="pa26-body">
            {mode === "add" ? "Добавить" : "Заменить на"}:{" "}
            <strong>{recipe.title}</strong>
          </p>
          {mealIndex != null && meals[mealIndex] ? (
            <p className={cn("pa26-caption text-pa-muted")}>
              Вместо: {meals[mealIndex].name} ({mealLabel(meals[mealIndex].meal_type)})
            </p>
          ) : null}
          {error ? <p className="pa26-caption text-pa-error">{error}</p> : null}
        </div>
      )}
    </BottomSheet2026>
  );
}
