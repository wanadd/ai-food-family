"use client";

import { useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import {
  V2BottomSheet,
  V2Button,
} from "@/components/planam-v2/ui/V2Primitives";
import { useTelegram } from "@/components/TelegramProvider";
import { invalidate as invalidateCache } from "@/lib/cache/session-cache";
import { createMealCheckin } from "@/lib/meal-checkins/api";
import { MEAL_TYPE_LABELS } from "@/lib/meal-checkins/constants";
import { createCookingBatch } from "@/lib/plan/leftovers-api";
import type { RecipeMealContext } from "@/lib/recipes/recipe-meal-context";
import { cn } from "@/lib/planam/cn";

export type RecipeCookFinishSheetProps = {
  open: boolean;
  onClose: () => void;
  onDone?: () => void;
  recipeId: number;
  recipeTitle: string;
  servings?: number;
  mealContext: RecipeMealContext;
  hasMenuContext: boolean;
};

export function RecipeCookFinishSheet({
  open,
  onClose,
  onDone,
  recipeId,
  recipeTitle,
  servings = 1,
  mealContext,
  hasMenuContext,
}: RecipeCookFinishSheetProps) {
  const { initData } = useTelegram();
  const { mode } = useAppMode();
  const [busy, setBusy] = useState<"eaten" | "later" | "pantry" | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const mealType =
    mealContext.mealType &&
    ["breakfast", "lunch", "dinner", "snack"].includes(mealContext.mealType)
      ? mealContext.mealType
      : "dinner";

  async function handleEatenNow() {
    if (!initData) {
      setError("Отметка доступна в Telegram Mini App");
      return;
    }
    setBusy("eaten");
    setError(null);
    try {
      await createMealCheckin(initData, mode, {
        meal_type: mealType,
        actual_status: "ate_home",
        planned_date: mealContext.plannedDate ?? undefined,
        actual_description: recipeTitle,
        recipe_id: recipeId,
      });
      invalidateCache("menu-overview");
      invalidateCache("progress-overview");
      setMessage(
        hasMenuContext
          ? `${MEAL_TYPE_LABELS[mealType] ?? "Приём"} отмечен как съеденный — здоровье обновится.`
          : "Блюдо отмечено как съеденное сегодня.",
      );
      onDone?.();
    } catch {
      setError("Не удалось отметить приём. Попробуйте в разделе «Здоровье».");
    } finally {
      setBusy(null);
    }
  }

  async function handleEatLater() {
    if (!initData) {
      setMessage("Блюдо не засчитано в питание. Отметьте позже в «Здоровье».");
      return;
    }
    setBusy("later");
    setError(null);
    try {
      await createMealCheckin(initData, mode, {
        meal_type: mealType,
        actual_status: "cooked",
        planned_date: mealContext.plannedDate ?? undefined,
        actual_description: recipeTitle,
        recipe_id: recipeId,
      });
      invalidateCache("menu-overview");
      setMessage(
        "Съедим позже — КБЖУ не учтены. Можно отметить, когда поедите.",
      );
      onDone?.();
    } catch {
      setMessage(
        "Блюдо не засчитано в питание. Добавление в остатки появится позже.",
      );
    } finally {
      setBusy(null);
    }
  }

  async function handleAddToPantry() {
    if (!initData) {
      setError("Запасы доступны в Telegram Mini App");
      return;
    }
    setBusy("pantry");
    setError(null);
    try {
      await createCookingBatch(initData, mode, {
        recipe_id: recipeId,
        recipe_title: recipeTitle,
        menu_selection_id: mealContext.menuSelectionId,
        day_index: mealContext.dayIndex,
        planned_date: mealContext.plannedDate,
        meal_type: mealContext.mealType,
        total_servings: servings,
        serving_unit: "порция",
      });
      await createMealCheckin(initData, mode, {
        meal_type: mealType,
        actual_status: "cooked",
        planned_date: mealContext.plannedDate ?? undefined,
        actual_description: recipeTitle,
        recipe_id: recipeId,
      });
      invalidateCache("menu-overview");
      setMessage("Готовое блюдо сохранено в запасах. КБЖУ не учтены.");
      onDone?.();
    } catch {
      setError("Не удалось сохранить в запасы. Попробуйте позже.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <V2BottomSheet open={open} title="Готово" onClose={onClose}>
      <div className="space-y-3 pb-2" data-testid="recipe-cook-finish-sheet">
        <p className="pa26-body text-pa-muted">Что сделать с блюдом?</p>
        <p className="pa26-micro text-pa-muted">
          Приготовленное не считается съеденным, пока вы не подтвердите это явно.
        </p>

        {message ? (
          <p className="rounded-control border border-sage-200 bg-sage-50 px-3 py-2 pa26-caption text-sage-800 dark:border-sage-700/40 dark:bg-sage-900/20">
            {message}
          </p>
        ) : null}
        {error ? (
          <p className="pa26-caption text-pa-error">{error}</p>
        ) : null}

        <OutcomeButton
          label="Съели сейчас"
          caption="Обновит здоровье и отметит приём пищи съеденным"
          disabled={Boolean(busy) || Boolean(message)}
          loading={busy === "eaten"}
          onClick={() => void handleEatenNow()}
          data-testid="recipe-finish-eaten"
        />
        <OutcomeButton
          label="Съедим позже"
          caption="Не засчитывает КБЖУ сейчас"
          disabled={Boolean(busy) || Boolean(message)}
          loading={busy === "later"}
          onClick={() => void handleEatLater()}
          data-testid="recipe-finish-later"
        />
        <OutcomeButton
          label="Добавить в запасы"
          caption="Сохранить как готовое блюдо"
          disabled={Boolean(busy) || Boolean(message)}
          loading={busy === "pantry"}
          onClick={() => void handleAddToPantry()}
          data-testid="recipe-finish-pantry"
        />
        <V2Button variant="ghost" size="wide" onClick={onClose}>
          Отмена
        </V2Button>
      </div>
    </V2BottomSheet>
  );
}

function OutcomeButton({
  label,
  caption,
  onClick,
  disabled,
  loading,
  "data-testid": testId,
}: {
  label: string;
  caption: string;
  onClick: () => void;
  disabled?: boolean;
  loading?: boolean;
  "data-testid"?: string;
}) {
  return (
    <button
      type="button"
      data-testid={testId}
      disabled={disabled || loading}
      onClick={onClick}
      className={cn(
        "flex w-full min-h-[56px] flex-col justify-center rounded-card border border-pa-border bg-pa-surface px-4 py-3 text-left transition",
        "hover:bg-orange-50/60 disabled:opacity-60 dark:hover:bg-pa-elevated/40",
      )}
    >
      <span className="pa26-card-title">{loading ? "Сохраняем…" : label}</span>
      <span className="pa26-micro mt-0.5 text-pa-muted">{caption}</span>
    </button>
  );
}
