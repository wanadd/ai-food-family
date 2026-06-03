"use client";

import { useCallback, useEffect, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { BottomSheet2026 } from "@/components/planam-2026/ui/BottomSheet2026";
import { Button2026 } from "@/components/planam-2026/ui/Button2026";
import { useTelegram } from "@/components/TelegramProvider";
import { invalidate as invalidateCache } from "@/lib/cache/session-cache";
import { createMealCheckin } from "@/lib/meal-checkins/api";
import { MEAL_TYPE_LABELS } from "@/lib/meal-checkins/constants";
import { fetchSelectedMenu } from "@/lib/menu/api";
import { getMenuDays, mealsForDayIndex } from "@/lib/menu/menu-days";
import type { MenuMeal } from "@/lib/menu/types";
import { cn } from "@/lib/planam/cn";

type MealOutcomeSheet2026Props = {
  open: boolean;
  onClose: () => void;
  onSuccess?: () => void;
};

type Step = "meal" | "portions" | "done";

const PORTION_OPTIONS = [0, 1, 2, 3, 4, 5, 6];

export function MealOutcomeSheet2026({
  open,
  onClose,
  onSuccess,
}: MealOutcomeSheet2026Props) {
  const { initData } = useTelegram();
  const { mode } = useAppMode();
  const [step, setStep] = useState<Step>("meal");
  const [meals, setMeals] = useState<MenuMeal[]>([]);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<MenuMeal | null>(null);
  const [portions, setPortions] = useState(0);

  const todayIso = new Date().toISOString().slice(0, 10);

  const loadMeals = useCallback(async () => {
    if (!initData) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const selectedMenu = await fetchSelectedMenu(initData, mode);
      const menu = selectedMenu?.menu;
      if (!menu) {
        setMeals([]);
        return;
      }
      const days = getMenuDays(menu);
      const today =
        days.find((d) => d.date_iso === todayIso) ?? days[0];
      const dayMeals = today
        ? mealsForDayIndex(menu, today.day_index)
        : menu.meals ?? [];
      setMeals(
        dayMeals.filter((m) =>
          ["breakfast", "lunch", "dinner", "snack"].includes(m.meal_type),
        ),
      );
    } catch {
      setMeals([]);
      setError("Сначала создайте меню на неделю.");
    } finally {
      setLoading(false);
    }
  }, [initData, mode, todayIso]);

  useEffect(() => {
    if (open) {
      setStep("meal");
      setSelected(null);
      setPortions(0);
      setError(null);
      void loadMeals();
    }
  }, [open, loadMeals]);

  async function handleSubmit() {
    if (!initData || !selected) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const hasLeftovers = portions > 0;
      await createMealCheckin(initData, mode, {
        meal_type: selected.meal_type,
        actual_status: hasLeftovers ? "saved_as_leftover" : "ate_home",
        planned_date: todayIso,
        actual_description: selected.name,
        recipe_id: selected.recipe_id ?? undefined,
        leftover_servings_delta: hasLeftovers ? portions : null,
        leftover_status: hasLeftovers ? "active" : null,
      });
      invalidateCache("menu-overview");
      invalidateCache("pantry");
      setStep("done");
      onSuccess?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось сохранить");
    } finally {
      setBusy(false);
    }
  }

  const footer =
    step === "portions" ? (
      <Button2026
        variant="primary"
        className="w-full"
        loading={busy}
        onClick={() => void handleSubmit()}
      >
        Сохранить
      </Button2026>
    ) : step === "done" ? (
      <Button2026 variant="primary" className="w-full" onClick={onClose}>
        Готово
      </Button2026>
    ) : null;

  return (
    <BottomSheet2026
      open={open}
      title="Результат дня"
      onClose={onClose}
      footer={footer}
    >
      {step === "meal" ? (
        <div className="space-y-3">
          <p className="pa26-body text-pa-muted">Что приготовили?</p>
          {loading ? (
            <p className="pa26-caption text-pa-muted">Загружаем меню…</p>
          ) : meals.length === 0 ? (
            <p className="pa26-body text-pa-muted">
              {error ?? "Нет блюд на сегодня в плане."}
            </p>
          ) : (
            meals.map((meal) => (
              <button
                key={meal.meal_type}
                type="button"
                onClick={() => {
                  setSelected(meal);
                  setStep("portions");
                }}
                className="flex w-full flex-col rounded-card border border-pa-border bg-pa-surface px-4 py-3 text-left transition hover:bg-sage-50 dark:hover:bg-white/5"
              >
                <span className="pa26-micro text-pa-muted">
                  {MEAL_TYPE_LABELS[meal.meal_type] ?? meal.meal_type}
                </span>
                <span className="pa26-card-title">{meal.name}</span>
              </button>
            ))
          )}
        </div>
      ) : null}

      {step === "portions" && selected ? (
        <div className="space-y-4">
          <p className="pa26-body">
            <strong>{selected.name}</strong> — сколько порций осталось?
          </p>
          <div className="flex flex-wrap gap-2">
            {PORTION_OPTIONS.map((n) => (
              <button
                key={n}
                type="button"
                onClick={() => setPortions(n)}
                className={cn(
                  "min-w-[44px] rounded-control border px-3 py-2 pa26-body font-semibold",
                  portions === n
                    ? "border-sage-500 bg-sage-500 text-white dark:bg-sage-400"
                    : "border-pa-border bg-pa-surface text-pa-foreground",
                )}
              >
                {n === 0 ? "Нет" : n}
              </button>
            ))}
          </div>
          {portions > 0 ? (
            <p className="pa26-caption text-pa-muted">
              Остатки попадут в «Дом» и обновят запасы.
            </p>
          ) : (
            <p className="pa26-caption text-pa-muted">
              Отметим, что поели дома без остатков.
            </p>
          )}
          {error ? <p className="pa26-caption text-pa-error">{error}</p> : null}
          <button
            type="button"
            className="pa26-caption font-semibold text-sage-700 dark:text-sage-300"
            onClick={() => setStep("meal")}
          >
            ← Другое блюдо
          </button>
        </div>
      ) : null}

      {step === "done" ? (
        <p className="pa26-body text-pa-muted">
          Спасибо! План и запасы обновлены.
        </p>
      ) : null}
    </BottomSheet2026>
  );
}
