"use client";

import { useEffect, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { V2BottomSheet } from "@/components/planam-v2/ui/V2Primitives";
import { useTelegram } from "@/components/TelegramProvider";
import { menuMealHeading } from "@/lib/menu/meal-heading";
import { fetchMenuDayNutrition } from "@/lib/menu/api";
import {
  DAY_SUMMARY_SHEET_SUBTITLE,
  DAY_SUMMARY_SHEET_TITLE,
  formatDaySummaryKcal,
} from "@/lib/plan/day-summary-sheet";
import { mealTypeLabel } from "@/lib/plan/plan-today";
import type { PlanTodayMeal } from "@/lib/plan/plan-today";

type DaySummarySheetV2Props = {
  open: boolean;
  onClose: () => void;
  plannedDate: string;
  meals: PlanTodayMeal[];
};

function Macro({ label, value }: { label: string; value: number }) {
  return (
    <div className="text-center">
      <p className="pa26-caption font-semibold text-pa-foreground">{value} г</p>
      <p className="pa26-micro mt-0.5 text-pa-muted">{label}</p>
    </div>
  );
}

export function DaySummarySheetV2({
  open,
  onClose,
  plannedDate,
  meals,
}: DaySummarySheetV2Props) {
  const { initData } = useTelegram();
  const { mode } = useAppMode();
  const [loading, setLoading] = useState(false);
  const [nutrition, setNutrition] = useState<
    Awaited<ReturnType<typeof fetchMenuDayNutrition>>
  >(null);

  useEffect(() => {
    if (!open || !initData || !plannedDate) {
      return;
    }
    let active = true;
    setLoading(true);
    fetchMenuDayNutrition(initData, mode, plannedDate)
      .then((data) => {
        if (active) {
          setNutrition(data);
        }
      })
      .catch(() => {
        if (active) {
          setNutrition(null);
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, [open, initData, mode, plannedDate]);

  const approximate =
    nutrition?.confidence === "estimated" ||
    nutrition?.confidence === "low_confidence";

  const plannedKcal = meals.reduce((sum, item) => {
    const kcal = item.meal.calories_estimate;
    return sum + (kcal != null && kcal > 0 ? kcal : 0);
  }, 0);

  const displayKcal = nutrition?.totals.kcal ?? plannedKcal;
  const targetKcal = nutrition?.targets.kcal ?? null;

  return (
    <V2BottomSheet open={open} title={DAY_SUMMARY_SHEET_TITLE} onClose={onClose}>
      <div className="space-y-4 pb-2">
        <p className="pa26-caption -mt-1 text-pa-muted">{DAY_SUMMARY_SHEET_SUBTITLE}</p>

        {loading ? (
          <p className="pa26-body text-pa-muted">Считаем КБЖУ…</p>
        ) : nutrition?.confidence === "unavailable" ? (
          <p className="pa26-body text-pa-muted">
            КБЖУ пока нельзя посчитать — часть рецептов требует уточнения
          </p>
        ) : (
          <div className="rounded-card border border-pa-border bg-pa-surface p-4">
            <p className="pa26-hero text-pa-foreground">
              {formatDaySummaryKcal(displayKcal, targetKcal, approximate)}
            </p>
            {nutrition ? (
              <div className="mt-3 grid grid-cols-3 gap-2">
                <Macro label="Белки" value={nutrition.totals.protein} />
                <Macro label="Жиры" value={nutrition.totals.fat} />
                <Macro label="Углеводы" value={nutrition.totals.carbs} />
              </div>
            ) : plannedKcal > 0 ? (
              <p className="mt-2 pa26-micro text-pa-muted">
                Макросы появятся, когда рецепты будут с полным КБЖУ
              </p>
            ) : null}
            {nutrition?.warnings[0] ? (
              <p className="mt-3 pa26-micro text-pa-muted">{nutrition.warnings[0]}</p>
            ) : null}
          </div>
        )}

        {meals.length > 0 ? (
          <div>
            <p className="pa26-caption font-semibold text-pa-foreground">Блюда дня</p>
            <ul className="mt-2 space-y-2">
              {meals.map((item) => {
                const heading = menuMealHeading(item.meal);
                const type = mealTypeLabel(item.meal.meal_type);
                const kcal =
                  item.meal.calories_estimate != null && item.meal.calories_estimate > 0
                    ? `${Math.round(item.meal.calories_estimate)} ккал`
                    : null;
                const parts = [type, heading, kcal].filter(Boolean);
                return (
                  <li
                    key={`${item.meal.meal_type}-${item.mealIndex}`}
                    className="pa26-body text-pa-foreground"
                  >
                    {parts.join(" · ")}
                  </li>
                );
              })}
            </ul>
          </div>
        ) : (
          <p className="pa26-body text-pa-muted">На этот день блюд в плане нет.</p>
        )}
      </div>
    </V2BottomSheet>
  );
}
