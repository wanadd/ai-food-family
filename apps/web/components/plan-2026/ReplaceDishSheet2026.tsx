"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { BottomSheet2026 } from "@/components/planam-2026/ui/BottomSheet2026";
import { useSubscriptionOverview } from "@/components/subscription/SubscriptionProvider";
import { useTelegram } from "@/components/TelegramProvider";
import {
  cacheKey,
  invalidate as invalidateCache,
  setCached,
} from "@/lib/cache/session-cache";
import { mealTypeLabel } from "@/lib/plan/plan-today";
import { replaceDish, selectMenu } from "@/lib/menu/api";
import { mergeReplaceResult, menuViewForDay } from "@/lib/menu/menu-days";
import { MEAL_LABELS } from "@/lib/menu/labels";
import type { MenuVariant } from "@/lib/menu/types";

const AmaConfirmDialog = dynamic(
  () =>
    import("@/components/subscription/AmaConfirmDialog").then(
      (m) => m.AmaConfirmDialog,
    ),
  { ssr: false },
);

type ReplaceDishSheet2026Props = {
  open: boolean;
  menu: MenuVariant | null;
  dayIndex: number;
  preselectedMealIndex?: number | null;
  onClose: () => void;
  onSuccess?: () => void;
};

/**
 * AI replace via POST /menus/replace-dish (not slot assign).
 * Gap: optional hint/reason field from Master Spec — not in API payload UI yet.
 */
export function ReplaceDishSheet2026({
  open,
  menu,
  dayIndex,
  preselectedMealIndex = null,
  onClose,
  onSuccess,
}: ReplaceDishSheet2026Props) {
  const { initData } = useTelegram();
  const { mode } = useAppMode();
  const [mealIndex, setMealIndex] = useState<number | null>(null);
  const [replacing, setReplacing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const {
    overview: subscription,
    ensureLoaded,
    refresh: refreshSubscription,
  } = useSubscriptionOverview();

  useEffect(() => {
    if (!open) {
      setMealIndex(null);
      setError(null);
      return;
    }
    if (preselectedMealIndex != null) {
      setMealIndex(preselectedMealIndex);
    }
    if (initData) {
      void ensureLoaded();
    }
  }, [open, preselectedMealIndex, initData, ensureLoaded]);

  const dayMenu = menu ? menuViewForDay(menu, dayIndex) : null;
  const amaBalance = subscription?.ama_balance ?? null;
  const amaCosts = subscription?.ama_costs ?? null;
  const selectedMeal =
    dayMenu && mealIndex != null ? dayMenu.meals[mealIndex] : null;

  async function handleConfirmReplace() {
    if (!initData || !menu || !dayMenu || mealIndex == null) {
      return;
    }
    setReplacing(true);
    setError(null);
    try {
      const updated = await replaceDish(
        initData,
        mode,
        dayMenu,
        mealIndex,
        undefined,
        dayIndex,
      );
      const merged = mergeReplaceResult(menu, updated, dayIndex);
      await selectMenu(initData, mode, merged);
      invalidateCache("selected-menu");
      invalidateCache("menu-overview");
      invalidateCache("shopping-list");
      invalidateCache("pantry");
      setCached(cacheKey.selectedMenu(mode), {
        menu: merged,
        selected_at: new Date().toISOString(),
      });
      onSuccess?.();
      onClose();
      void refreshSubscription();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Не удалось заменить блюдо. Попробуйте ещё раз.",
      );
    } finally {
      setReplacing(false);
    }
  }

  function handleCancelConfirm() {
    if (replacing) {
      return;
    }
    setMealIndex(null);
    if (preselectedMealIndex != null) {
      onClose();
    }
  }

  return (
    <>
      <BottomSheet2026
        open={open && mealIndex === null}
        title="Заменить блюдо"
        onClose={onClose}
      >
        {!dayMenu ? (
          <p className="pa26-body text-pa-muted">Сначала создайте план на неделю.</p>
        ) : (
          <div className="space-y-2">
            <p className="pa26-caption text-pa-muted">
              ПланАм подберёт альтернативу (AI). Стоимость в Амах — на следующем шаге.
            </p>
            {dayMenu.meals.map((meal, index) => (
              <button
                key={`${meal.meal_type}-${index}`}
                type="button"
                onClick={() => setMealIndex(index)}
                className="flex w-full flex-col rounded-card border border-pa-border bg-pa-surface px-4 py-3 text-left transition hover:bg-sage-50 dark:hover:bg-white/5"
              >
                <span className="pa26-micro text-pa-muted">
                  {MEAL_LABELS[meal.meal_type] ?? meal.meal_type}
                </span>
                <span className="pa26-card-title">{meal.name}</span>
              </button>
            ))}
          </div>
        )}
      </BottomSheet2026>

      <AmaConfirmDialog
        open={open && mealIndex !== null}
        title="Подтвердить замену"
        description={
          selectedMeal ? (
            <span>
              Новое блюдо вместо «{selectedMeal.name}» (
              {mealTypeLabel(selectedMeal.meal_type)}).
            </span>
          ) : null
        }
        benefit="ПланАм обновит план и список покупок"
        costAma={amaCosts?.menu_replace_dish ?? null}
        balanceAma={amaBalance}
        busy={replacing}
        confirmLabel="Заменить"
        onCancel={handleCancelConfirm}
        onConfirm={() => void handleConfirmReplace()}
      />

      {error ? (
        <p className="fixed bottom-24 left-4 right-4 z-[60] rounded-card border border-pa-error/30 bg-pa-surface px-3 py-2 pa26-caption text-pa-error">
          {error}
        </p>
      ) : null}
    </>
  );
}
