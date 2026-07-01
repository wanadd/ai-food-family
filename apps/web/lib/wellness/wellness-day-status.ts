import type { MealCheckin } from "@/lib/meal-checkins/api";
import type { MenuOverview } from "@/lib/menu/overview-types";
import type { ProgressOverview } from "@/lib/progress/types";

const EATEN = new Set([
  "ate_home",
  "ate_work",
  "ate_cafe",
  "ate_restaurant",
  "ate_delivery",
  "ate_other",
  "completed",
]);

const DEVIATION = new Set(["skipped", "ate_other"]);

export type WellnessDayStatusId =
  | "on_plan"
  | "deviations"
  | "needs_checkin";

export type WellnessDayStatus = {
  id: WellnessDayStatusId;
  label: string;
};

function latestCheckinByMeal(
  checkins: MealCheckin[],
): Map<string, MealCheckin> {
  const map = new Map<string, MealCheckin>();
  for (const row of checkins) {
    const prev = map.get(row.meal_type);
    if (!prev || row.created_at > prev.created_at) {
      map.set(row.meal_type, row);
    }
  }
  return map;
}

export function buildWellnessDayStatus(input: {
  overview: MenuOverview | null;
  progress: ProgressOverview | null;
  checkins: MealCheckin[];
}): WellnessDayStatus {
  const { overview, checkins } = input;
  const planned =
    overview?.today_meals.filter((m) => m.name?.trim()) ?? [];
  const byMeal = latestCheckinByMeal(checkins);

  if (planned.length === 0) {
    return { id: "needs_checkin", label: "Составьте меню на сегодня" };
  }

  let hasDeviation = false;
  let needsConfirmation = false;

  for (const meal of planned) {
    const row = byMeal.get(meal.meal_type);
    if (!row) {
      needsConfirmation = true;
      continue;
    }
    if (DEVIATION.has(row.actual_status)) {
      hasDeviation = true;
    }
    if (row.actual_status === "cooked") {
      needsConfirmation = true;
    }
    if (!EATEN.has(row.actual_status) && row.actual_status !== "skipped") {
      needsConfirmation = true;
    }
  }

  for (const row of checkins) {
    if (DEVIATION.has(row.actual_status)) {
      hasDeviation = true;
    }
  }

  if (hasDeviation) {
    return { id: "deviations", label: "Есть отклонения" };
  }
  if (needsConfirmation) {
    return { id: "needs_checkin", label: "Нужно уточнить приём пищи" };
  }

  const eatenCount = Array.from(byMeal.values()).filter((r) =>
    EATEN.has(r.actual_status),
  ).length;
  if (eatenCount >= planned.length && planned.length > 0) {
    return { id: "on_plan", label: "Идёте по плану" };
  }

  return { id: "on_plan", label: "Идёте по плану" };
}

export function formatWellnessDate(date = new Date()): string {
  return date.toLocaleDateString("ru-RU", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });
}
