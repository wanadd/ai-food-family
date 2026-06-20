import type { MealConsumptionNutritionSummary } from "./meal-consumption-api";

export const CONSUMPTION_NUTRITION_FORBIDDEN_PHRASES = [
  "Итог дня",
  "Результат дня",
  "Что приготовили?",
  "Показать итог дня",
] as const;

export type ConsumptionNutritionCardLines = {
  headlineKcal: string;
  macroLine: string;
  loggedLine: string | null;
  plannedReferenceLine: string | null;
  ateOutLine: string | null;
  skippedLine: string | null;
  mode: "planned" | "actual";
};

export function buildConsumptionNutritionCardLines(
  summary: MealConsumptionNutritionSummary,
  targetKcal: number | null,
): ConsumptionNutritionCardLines {
  if (summary.mode !== "actual" || !summary.actual) {
    const kcal = summary.planned.calories;
    const headline = targetKcal
      ? `${kcal} / ${targetKcal} ккал`
      : `${kcal} ккал`;
    return {
      mode: "planned",
      headlineKcal: headline,
      macroLine: `Б ${summary.planned.protein} г · Ж ${summary.planned.fat} г · У ${summary.planned.carbs} г`,
      loggedLine: "Факт: пока нет отметок",
      plannedReferenceLine: null,
      ateOutLine: null,
      skippedLine: null,
    };
  }

  const actual = summary.actual;
  const headline = targetKcal
    ? `${actual.calories} / ${targetKcal} ккал`
    : `${actual.calories} ккал`;

  const loggedLine =
    summary.counts.planned_meals > 0
      ? `Отмечено ${summary.counts.logged_meals} из ${summary.counts.planned_meals} блюд`
      : summary.counts.logged_meals > 0
        ? `Отмечено ${summary.counts.logged_meals} блюд`
        : null;

  return {
    mode: "actual",
    headlineKcal: headline,
    macroLine: `Б ${actual.protein} г · Ж ${actual.fat} г · У ${actual.carbs} г`,
    loggedLine,
    plannedReferenceLine: `План дня: ${summary.planned.calories} ккал`,
    ateOutLine:
      summary.counts.ate_out > 0
        ? `${summary.counts.ate_out} вне дома`
        : null,
    skippedLine:
      summary.counts.skipped > 0
        ? `${summary.counts.skipped} пропущено`
        : null,
  };
}

export function consumptionNutritionCardCopy(
  lines: ConsumptionNutritionCardLines,
): string {
  return [
    "Питание сегодня",
    lines.mode === "actual" ? "Съедено" : "",
    lines.headlineKcal,
    lines.macroLine,
    lines.loggedLine,
    lines.plannedReferenceLine,
    lines.ateOutLine,
    lines.skippedLine,
  ]
    .filter(Boolean)
    .join(" ");
}
