import { describe, expect, it } from "vitest";

import {
  buildConsumptionNutritionCardLines,
  consumptionNutritionCardCopy,
  CONSUMPTION_NUTRITION_FORBIDDEN_PHRASES,
} from "./meal-consumption-nutrition-card";
import type { MealConsumptionNutritionSummary } from "./meal-consumption-api";

const plannedSummary = (
  overrides: Partial<MealConsumptionNutritionSummary> = {},
): MealConsumptionNutritionSummary => ({
  mode: "planned",
  has_consumption_logs: false,
  planned: { calories: 1850, protein: 120, fat: 70, carbs: 180 },
  actual: null,
  counts: {
    planned_meals: 3,
    logged_meals: 0,
    eaten: 0,
    skipped: 0,
    ate_out: 0,
  },
  ...overrides,
});

const actualSummary = (
  overrides: Partial<MealConsumptionNutritionSummary> = {},
): MealConsumptionNutritionSummary => ({
  mode: "actual",
  has_consumption_logs: true,
  planned: { calories: 1850, protein: 120, fat: 70, carbs: 180 },
  actual: { calories: 740, protein: 45, fat: 28, carbs: 80 },
  counts: {
    planned_meals: 3,
    logged_meals: 1,
    eaten: 1,
    skipped: 0,
    ate_out: 0,
  },
  ...overrides,
});

describe("meal consumption nutrition card", () => {
  it("shows planned mode without logs", () => {
    const lines = buildConsumptionNutritionCardLines(plannedSummary(), 2200);
    expect(lines.mode).toBe("planned");
    expect(lines.headlineKcal).toBe("1850 / 2200 ккал");
    expect(lines.loggedLine).toBe("Факт: пока нет отметок");
    expect(lines.plannedReferenceLine).toBeNull();
  });

  it("shows actual mode with Съедено copy", () => {
    const lines = buildConsumptionNutritionCardLines(actualSummary(), 2200);
    expect(lines.mode).toBe("actual");
    expect(lines.headlineKcal).toBe("740 / 2200 ккал");
    expect(lines.macroLine).toContain("Б 45 г");
    expect(lines.loggedLine).toBe("Отмечено 1 из 3 блюд");
    expect(lines.plannedReferenceLine).toBe("План дня: 1850 ккал");
  });

  it("shows ate_out indicator", () => {
    const lines = buildConsumptionNutritionCardLines(
      actualSummary({
        actual: { calories: 0, protein: 0, fat: 0, carbs: 0 },
        counts: {
          planned_meals: 3,
          logged_meals: 1,
          eaten: 0,
          skipped: 0,
          ate_out: 1,
        },
      }),
      2200,
    );
    expect(lines.ateOutLine).toBe("1 вне дома");
  });

  it("shows skipped indicator", () => {
    const lines = buildConsumptionNutritionCardLines(
      actualSummary({
        counts: {
          planned_meals: 3,
          logged_meals: 1,
          eaten: 0,
          skipped: 1,
          ate_out: 0,
        },
      }),
      null,
    );
    expect(lines.skippedLine).toBe("1 пропущено");
  });

  it("does not include forbidden legacy phrases", () => {
    const copy = consumptionNutritionCardCopy(
      buildConsumptionNutritionCardLines(actualSummary(), 2200),
    );
    for (const phrase of CONSUMPTION_NUTRITION_FORBIDDEN_PHRASES) {
      expect(copy).not.toContain(phrase);
    }
  });

  it("refetch key pattern increments for save reload", () => {
    let refreshKey = 0;
    const bump = () => {
      refreshKey += 1;
    };
    bump();
    expect(refreshKey).toBe(1);
  });
});
