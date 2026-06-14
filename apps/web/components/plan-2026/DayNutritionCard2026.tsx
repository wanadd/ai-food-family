"use client";

import { useCallback, useEffect, useState } from "react";

import { Card2026 } from "@/components/planam-2026/ui/Card2026";
import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { useTelegram } from "@/components/TelegramProvider";
import { fetchMenuDayNutrition, type DayNutrition } from "@/lib/menu/api";
import { fetchMealConsumptionNutritionSummary } from "@/lib/plan/meal-consumption-api";
import {
  buildConsumptionNutritionCardLines,
  type ConsumptionNutritionCardLines,
} from "@/lib/plan/meal-consumption-nutrition-card";

type Props = {
  /** ISO date (YYYY-MM-DD) for the selected plan day. */
  plannedDate: string;
  familyId?: number | null;
  menuSelectionId?: number | null;
  dayIndex?: number | null;
  /** Increment to refetch after consumption save. */
  refreshKey?: number;
};

function confidenceHint(day: DayNutrition): string | null {
  switch (day.confidence) {
    case "estimated":
      return "примерно";
    case "low_confidence":
      return "часть рецептов требует уточнения";
    default:
      return null;
  }
}

function MacroInline({ label, value }: { label: string; value: number }) {
  return (
    <span>
      {label} {value} г
    </span>
  );
}

function PlannedCardBody({
  day,
  lines,
}: {
  day: DayNutrition;
  lines: ConsumptionNutritionCardLines;
}) {
  const isEmpty = day.coverage.total_items === 0;
  const approximate =
    day.confidence === "estimated" || day.confidence === "low_confidence";
  const hint = confidenceHint(day);
  const target = day.targets.kcal;
  const kcal = day.totals.kcal;

  if (isEmpty) {
    return (
      <p className="pa26-body mt-2 text-pa-muted">
        Добавьте блюда в меню, и я посчитаю КБЖУ
      </p>
    );
  }

  if (day.confidence === "unavailable") {
    return (
      <p className="pa26-body mt-2 text-pa-muted">
        КБЖУ пока нельзя посчитать — часть рецептов требует уточнения
      </p>
    );
  }

  return (
    <>
      <p className="pa26-hero mt-1 text-pa-foreground">
        {approximate ? "≈" : ""}
        {kcal}
        {target ? (
          <span className="pa26-body text-pa-muted"> / {target} ккал</span>
        ) : (
          <span className="pa26-body text-pa-muted"> ккал</span>
        )}
      </p>
      {hint ? (
        <p className="pa26-micro mt-1 text-pa-muted">По плану · {hint}</p>
      ) : (
        <p className="pa26-micro mt-1 text-pa-muted">По плану</p>
      )}
      {target ? (
        <div className="mt-2 h-2 w-full overflow-hidden rounded-pill bg-pa-elevated">
          <div
            className="h-full rounded-pill bg-pa-brand"
            style={{
              width: `${Math.min(100, Math.round((kcal / target) * 100))}%`,
            }}
          />
        </div>
      ) : null}
      <p className="pa26-caption mt-3 text-pa-muted">
        <MacroInline label="Б" value={day.totals.protein} />
        {" · "}
        <MacroInline label="Ж" value={day.totals.fat} />
        {" · "}
        <MacroInline label="У" value={day.totals.carbs} />
      </p>
      {day.warnings.length > 0 ? (
        <p className="mt-2 pa26-micro text-pa-muted">{day.warnings[0]}</p>
      ) : null}
    </>
  );
}

function ActualCardBody({
  lines,
  targetKcal,
}: {
  lines: ConsumptionNutritionCardLines;
  targetKcal: number | null;
}) {
  const kcal = Number(lines.headlineKcal.split(" ")[0]);

  return (
    <>
      <p className="pa26-micro mt-0.5 font-semibold text-sage-600 dark:text-sage-400">
        Съедено
      </p>
      <p className="pa26-hero mt-1 text-pa-foreground">
        {lines.headlineKcal}
        {!lines.headlineKcal.includes("ккал") ? (
          <span className="pa26-body text-pa-muted"> ккал</span>
        ) : null}
      </p>
      {targetKcal ? (
        <div className="mt-2 h-2 w-full overflow-hidden rounded-pill bg-pa-elevated">
          <div
            className="h-full rounded-pill bg-sage-500 dark:bg-sage-400"
            style={{
              width: `${Math.min(100, Math.round((kcal / targetKcal) * 100))}%`,
            }}
          />
        </div>
      ) : null}
      <p className="pa26-caption mt-3 text-pa-muted">{lines.macroLine}</p>
      {lines.loggedLine ? (
        <p className="pa26-micro mt-2 text-pa-muted">{lines.loggedLine}</p>
      ) : null}
      {lines.plannedReferenceLine ? (
        <p className="pa26-micro mt-1 text-pa-muted">{lines.plannedReferenceLine}</p>
      ) : null}
      {lines.ateOutLine ? (
        <p className="pa26-micro mt-1 text-pa-muted">{lines.ateOutLine}</p>
      ) : null}
      {lines.skippedLine ? (
        <p className="pa26-micro mt-1 text-pa-muted">{lines.skippedLine}</p>
      ) : null}
    </>
  );
}

export function DayNutritionCard2026({
  plannedDate,
  familyId,
  menuSelectionId,
  dayIndex,
  refreshKey = 0,
}: Props) {
  const { initData } = useTelegram();
  const { mode } = useAppMode();
  const [day, setDay] = useState<DayNutrition | null>(null);
  const [consumptionLines, setConsumptionLines] =
    useState<ConsumptionNutritionCardLines | null>(null);
  const [targetKcal, setTargetKcal] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!initData || !plannedDate) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      if (familyId != null) {
        const summary = await fetchMealConsumptionNutritionSummary(initData, mode, {
          family_id: familyId,
          menu_selection_id: menuSelectionId,
          day_index: dayIndex,
          planned_date: plannedDate,
        });
        const target = summary.targets?.kcal ?? null;
        setTargetKcal(target);
        setConsumptionLines(buildConsumptionNutritionCardLines(summary, target));
        if (summary.mode === "planned") {
          const plannedDay = await fetchMenuDayNutrition(initData, mode, plannedDate);
          setDay(plannedDay);
        } else {
          setDay(null);
        }
      } else {
        const plannedDay = await fetchMenuDayNutrition(initData, mode, plannedDate);
        setDay(plannedDay);
        setConsumptionLines(null);
        setTargetKcal(plannedDay?.targets.kcal ?? null);
      }
    } catch {
      const plannedDay = await fetchMenuDayNutrition(initData, mode, plannedDate).catch(
        () => null,
      );
      setDay(plannedDay);
      setConsumptionLines(null);
      setTargetKcal(plannedDay?.targets.kcal ?? null);
    } finally {
      setLoading(false);
    }
  }, [
    initData,
    mode,
    plannedDate,
    familyId,
    menuSelectionId,
    dayIndex,
  ]);

  useEffect(() => {
    void load();
  }, [load, refreshKey]);

  if (loading) {
    return null;
  }

  const showActual = consumptionLines?.mode === "actual";

  if (!showActual && !day) {
    return null;
  }

  const hint =
    !showActual && day ? confidenceHint(day) : null;

  return (
    <Card2026 padding="md" className="mt-3">
      <div className="flex items-baseline justify-between">
        <p className="pa26-caption font-semibold text-pa-foreground">
          Питание сегодня
        </p>
        {hint ? (
          <span className="pa26-micro text-pa-muted">{hint}</span>
        ) : null}
      </div>

      {showActual && consumptionLines ? (
        <ActualCardBody lines={consumptionLines} targetKcal={targetKcal} />
      ) : day ? (
        <PlannedCardBody
          day={day}
          lines={
            consumptionLines ??
            buildConsumptionNutritionCardLines(
              {
                mode: "planned",
                has_consumption_logs: false,
                planned: {
                  calories: day.totals.kcal,
                  protein: day.totals.protein,
                  fat: day.totals.fat,
                  carbs: day.totals.carbs,
                },
                actual: null,
                counts: {
                  planned_meals: day.coverage.total_items,
                  logged_meals: 0,
                  eaten: 0,
                  skipped: 0,
                  ate_out: 0,
                },
              },
              day.targets.kcal,
            )
          }
        />
      ) : null}
    </Card2026>
  );
}
