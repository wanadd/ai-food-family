import type { MealCheckin } from "@/lib/meal-checkins/api";
import type { MenuOverview } from "@/lib/menu/overview-types";
import type { ProgressOverview } from "@/lib/progress/types";
import type { WaterToday } from "@/lib/water-intake/api";

const EATEN = new Set([
  "ate_home",
  "ate_work",
  "ate_cafe",
  "ate_restaurant",
  "ate_delivery",
  "ate_other",
  "completed",
  "saved_as_leftover",
]);

export type WellnessTodayMetrics = {
  eatenLabel: string;
  remainingLabel: string;
  waterLabel: string;
  activityLabel: string;
};

export type WellnessDayProgress = {
  percent: number;
  label: string;
};

export function countCompletedMeals(checkins: MealCheckin[]): number {
  const types = new Set<string>();
  for (const row of checkins) {
    if (EATEN.has(row.actual_status)) {
      types.add(row.meal_type);
    }
  }
  return types.size;
}

export function buildWellnessTodayMetrics(input: {
  progress: ProgressOverview | null;
  water: WaterToday | null;
  checkins: MealCheckin[];
  overview: MenuOverview | null;
}): WellnessTodayMetrics {
  const { progress, water, checkins, overview } = input;
  const targets = progress?.targets;
  const actual = progress?.daily_actual;

  const calTarget = targets?.calories_target ?? null;
  const calEaten =
    actual?.meals_logged && actual.calories_consumed > 0
      ? actual.calories_consumed
      : 0;
  const calLeft =
    calTarget != null ? Math.max(0, calTarget - calEaten) : null;

  const eatenLabel =
    calEaten > 0
      ? `${Math.round(calEaten)} ккал`
      : countCompletedMeals(checkins) > 0
        ? `${countCompletedMeals(checkins)} приёма`
        : "Пока не отмечено";

  const remainingLabel =
    calLeft != null && calTarget != null
      ? calLeft > 0
        ? `${Math.round(calLeft)} ккал`
        : "План выполнен"
      : "—";

  const waterTotal = water?.total_ml ?? actual?.water_consumed_ml ?? 0;
  const waterTarget = water?.target_ml ?? targets?.water_target_ml ?? null;
  const waterLabel =
    waterTarget != null
      ? `${(waterTotal / 1000).toFixed(1)} / ${(waterTarget / 1000).toFixed(1)} л`
      : `${(waterTotal / 1000).toFixed(1)} л`;

  const trainings = progress?.trainings_this_week ?? 0;
  const minutes = progress?.training_minutes_week ?? 0;
  const activityLabel =
    trainings > 0
      ? `${trainings} трен.${minutes > 0 ? ` · ${minutes} мин` : ""}`
      : "Не отмечена на неделе";

  const plannedMeals = overview?.today_meals.filter((m) => m.name).length ?? 0;
  if (plannedMeals > 0 && countCompletedMeals(checkins) === 0 && calEaten === 0) {
    return {
      eatenLabel: "0 из плана",
      remainingLabel:
        calLeft != null ? `${Math.round(calLeft)} ккал` : `${plannedMeals} блюд`,
      waterLabel,
      activityLabel,
    };
  }

  return {
    eatenLabel,
    remainingLabel,
    waterLabel,
    activityLabel,
  };
}

export function buildWellnessDayProgress(input: {
  progress: ProgressOverview | null;
  water: WaterToday | null;
  checkins: MealCheckin[];
  overview: MenuOverview | null;
  /** When checkins are not loaded (e.g. Home chip). */
  mealsCompletedOverride?: number;
}): WellnessDayProgress {
  const { progress, water, checkins, overview, mealsCompletedOverride } =
    input;
  const targets = progress?.targets;
  const actual = progress?.daily_actual;

  const parts: number[] = [];

  const calTarget = targets?.calories_target;
  const calEaten = actual?.calories_consumed ?? 0;
  if (calTarget && calTarget > 0 && actual?.meals_logged) {
    parts.push(Math.min(100, Math.round((calEaten / calTarget) * 100)));
  }

  const waterTotal = water?.total_ml ?? actual?.water_consumed_ml ?? 0;
  const waterTarget = water?.target_ml ?? targets?.water_target_ml;
  if (waterTarget && waterTarget > 0) {
    parts.push(Math.min(100, Math.round((waterTotal / waterTarget) * 100)));
  }

  const planned = overview?.today_meals.filter((m) => m.name).length ?? 0;
  const done =
    mealsCompletedOverride ?? countCompletedMeals(checkins);
  if (planned > 0) {
    parts.push(Math.min(100, Math.round((done / planned) * 100)));
  } else if (done > 0) {
    parts.push(Math.min(100, done * 25));
  }

  const percent =
    parts.length > 0
      ? Math.round(parts.reduce((a, b) => a + b, 0) / parts.length)
      : 0;

  let label = "Начните с воды и отметки блюд";
  if (percent >= 85) {
    label = "Отличный день";
  } else if (percent >= 50) {
    label = "Хороший темп";
  } else if (percent > 0) {
    label = "День в процессе";
  }

  return { percent, label };
}
