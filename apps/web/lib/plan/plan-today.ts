import type { MealCheckin } from "@/lib/meal-checkins/api";
import { MEAL_CHECKIN_OPTIONS } from "@/lib/meal-checkins/constants";
import { MEAL_LABELS } from "@/lib/menu/labels";
import {
  dateIsoForDayIndex,
  defaultDayIndex,
  mealsForDayIndex,
} from "@/lib/menu/menu-days";
import type { MenuMeal, MenuVariant } from "@/lib/menu/types";
import type { MenuOverview } from "@/lib/menu/overview-types";

export type TimelineSlotId = "morning" | "day" | "evening" | "snacks";

export type TimelineSlot = {
  id: TimelineSlotId;
  label: string;
  emoji: string;
  mealTypes: string[];
};

export const PLAN_TIMELINE_SLOTS: TimelineSlot[] = [
  { id: "morning", label: "Утро", emoji: "🌅", mealTypes: ["breakfast"] },
  { id: "day", label: "День", emoji: "☀️", mealTypes: ["lunch"] },
  { id: "evening", label: "Вечер", emoji: "🌙", mealTypes: ["dinner"] },
  { id: "snacks", label: "Перекусы", emoji: "🍎", mealTypes: ["snack"] },
];

export type PlanTodayMeal = {
  meal: MenuMeal;
  mealIndex: number;
  slotId: string | null;
  imageUrl: string | null;
  statusLabel: string;
  statusCode: string | null;
};

export type PlanTodayTimelineGroup = {
  slot: TimelineSlot;
  meals: PlanTodayMeal[];
};

export function todayDayIndex(menu: MenuVariant): number {
  return defaultDayIndex(menu);
}

export function plannedDateForDay(menu: MenuVariant, dayIndex: number): string {
  return dateIsoForDayIndex(menu, dayIndex);
}

export function buildImageMapFromOverview(
  overview: MenuOverview | null,
): Map<string, string | null> {
  const map = new Map<string, string | null>();
  if (!overview) {
    return map;
  }
  for (const row of overview.today_meals) {
    if (row.meal_type && row.image_url) {
      map.set(row.meal_type, row.image_url);
    }
    if (row.meal_type && row.recipe_id != null) {
      map.set(`recipe:${row.recipe_id}`, row.image_url ?? null);
    }
  }
  return map;
}

export function enrichMealsForDay(
  menu: MenuVariant,
  dayIndex: number,
  checkins: MealCheckin[],
  imageByType: Map<string, string | null>,
  memberId: number | null = null,
): PlanTodayMeal[] {
  const meals = mealsForDayIndex(menu, dayIndex);
  const statusByType = new Map<string, string>();
  for (const row of checkins) {
    const rowMember = row.family_member_id ?? null;
    if (rowMember !== memberId) {
      continue;
    }
    statusByType.set(row.meal_type, row.actual_status);
  }

  const dateIso = dateIsoForDayIndex(menu, dayIndex);

  return meals
    .map((meal, mealIndex) => ({ meal, mealIndex }))
    .filter(
      ({ meal }) =>
        meal.recipe_id != null &&
        meal.name.trim() !== "" &&
        meal.name !== "Свободно",
    )
    .map(({ meal, mealIndex }) => {
    const statusCode = statusByType.get(meal.meal_type) ?? null;
    const statusLabel = statusCode
      ? (MEAL_CHECKIN_OPTIONS.find((o) => o.value === statusCode)?.label ??
        statusCode)
      : "В плане";
    const imageUrl =
      (meal.recipe_id != null
        ? imageByType.get(`recipe:${meal.recipe_id}`)
        : null) ??
      imageByType.get(meal.meal_type) ??
      null;

    return {
      meal,
      mealIndex,
      slotId: meal.slot_id ?? `${dateIso}:${meal.meal_type}`,
      imageUrl,
      statusLabel,
      statusCode,
    };
  });
}

export function groupByTimeline(meals: PlanTodayMeal[]): PlanTodayTimelineGroup[] {
  const groups: PlanTodayTimelineGroup[] = [];
  for (const slot of PLAN_TIMELINE_SLOTS) {
    const slotMeals = meals.filter((m) =>
      slot.mealTypes.includes(m.meal.meal_type),
    );
    if (slotMeals.length > 0) {
      groups.push({ slot, meals: slotMeals });
    }
  }
  const other = meals.filter(
    (m) => !PLAN_TIMELINE_SLOTS.some((s) => s.mealTypes.includes(m.meal.meal_type)),
  );
  if (other.length > 0) {
    groups.push({
      slot: {
        id: "snacks",
        label: "Другое",
        emoji: "🍽",
        mealTypes: [],
      },
      meals: other,
    });
  }
  return groups;
}

export function formatPlanDayLabel(menu: MenuVariant, dayIndex: number): string {
  const iso = dateIsoForDayIndex(menu, dayIndex);
  const d = new Date(iso);
  const today = new Date().toISOString().slice(0, 10);
  if (iso === today) {
    return "Сегодня";
  }
  return d.toLocaleDateString("ru-RU", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });
}

export function mealTypeLabel(mealType: string): string {
  return MEAL_LABELS[mealType as keyof typeof MEAL_LABELS] ?? mealType;
}
