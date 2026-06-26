import type { MealCheckin } from "@/lib/meal-checkins/api";
import { MEAL_TYPE_LABELS } from "@/lib/meal-checkins/constants";
import type { MenuOverview } from "@/lib/menu/overview-types";

const MEAL_ORDER = ["breakfast", "lunch", "dinner", "snack"] as const;

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

export type MealSlotStatus =
  | "none"
  | "planned"
  | "eaten"
  | "skipped"
  | "later"
  | "other";

export type WellnessMealSlot = {
  mealType: string;
  label: string;
  plannedName: string | null;
  recipeId: number | null;
  status: MealSlotStatus;
  statusLabel: string;
};

function statusFromCheckin(
  checkin: MealCheckin | undefined,
): { status: MealSlotStatus; statusLabel: string } {
  if (!checkin) {
    return { status: "none", statusLabel: "Не отмечено" };
  }
  const s = checkin.actual_status;
  if (EATEN.has(s) && s === "ate_other") {
    return { status: "other", statusLabel: "Ел другое" };
  }
  if (EATEN.has(s)) {
    return { status: "eaten", statusLabel: "Съедено" };
  }
  if (s === "skipped") {
    return { status: "skipped", statusLabel: "Пропущено" };
  }
  if (s === "cooked") {
    return { status: "later", statusLabel: "Съем позже" };
  }
  return { status: "planned", statusLabel: "В плане" };
}

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

export function buildWellnessMealSlots(input: {
  overview: MenuOverview | null;
  checkins: MealCheckin[];
}): WellnessMealSlot[] {
  const { overview, checkins } = input;
  const plannedByType = new Map(
    (overview?.today_meals ?? []).map((m) => [m.meal_type, m]),
  );
  const checkinByType = latestCheckinByMeal(checkins);

  const types =
    plannedByType.size > 0
      ? MEAL_ORDER.filter((t) => plannedByType.has(t))
      : [...MEAL_ORDER];

  return types.map((mealType) => {
    const planned = plannedByType.get(mealType);
    const checkin = checkinByType.get(mealType);
    const resolved = statusFromCheckin(checkin);

    let status = resolved.status;
    let statusLabel = resolved.statusLabel;

    if (status === "none" && planned?.name) {
      status = "planned";
      statusLabel = "Запланировано";
    }

    return {
      mealType,
      label: MEAL_TYPE_LABELS[mealType] ?? planned?.label ?? mealType,
      plannedName: planned?.name ?? null,
      recipeId: planned?.recipe_id ?? null,
      status,
      statusLabel,
    };
  });
}
