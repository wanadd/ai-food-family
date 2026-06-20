import {
  dateIsoForDayIndex,
  defaultDayIndex,
  getMenuDays,
  mealsForDayIndex,
} from "@/lib/menu/menu-days";
import type { MenuMeal, MenuVariant } from "@/lib/menu/types";
import type { MenuOverview } from "@/lib/menu/overview-types";

export function userLocalDateIso(now: Date = new Date()): string {
  return now.toISOString().slice(0, 10);
}

export function resolveActiveMenuDayIndex(
  menu: MenuVariant | null | undefined,
  now: Date = new Date(),
): number {
  if (!menu) return 1;
  return defaultDayIndex(menu);
}

export type ActiveMenuDayState = {
  currentDate: string;
  activeMenuDayIndex: number;
  activeMenuDate: string;
  activeMeals: MenuMeal[];
  hasMenuForToday: boolean;
  menuPlanStartDate: string | null;
  menuPlanEndDate: string | null;
};

export function buildActiveMenuDayState(
  overview: MenuOverview | null | undefined,
  now: Date = new Date(),
): ActiveMenuDayState {
  const currentDate = userLocalDateIso(now);
  const menu = overview?.selected_menu?.menu ?? null;
  const activeMenuDayIndex = resolveActiveMenuDayIndex(menu, now);
  const activeMenuDate = menu
    ? dateIsoForDayIndex(menu, activeMenuDayIndex)
    : currentDate;
  const activeMeals = menu ? mealsForDayIndex(menu, activeMenuDayIndex) : [];
  const days = menu ? getMenuDays(menu) : [];
  const dates = days.map((d) => d.date_iso).filter(Boolean);
  const sorted = dates.slice().sort();

  return {
    currentDate,
    activeMenuDayIndex,
    activeMenuDate,
    activeMeals,
    hasMenuForToday: activeMenuDate === currentDate && activeMeals.some((m) => m.name?.trim()),
    menuPlanStartDate: sorted[0] ?? null,
    menuPlanEndDate: sorted[sorted.length - 1] ?? null,
  };
}

export function sumMealNutrition(meals: MenuMeal[]): {
  calories: number;
  protein_g: number;
  fat_g: number;
  carbs_g: number;
} {
  let calories = 0;
  let protein_g = 0;
  let fat_g = 0;
  let carbs_g = 0;
  for (const meal of meals) {
    if (meal.calories_estimate != null) calories += meal.calories_estimate;
    if (meal.protein_g != null) protein_g += meal.protein_g;
    if (meal.fat_g != null) fat_g += meal.fat_g;
    if (meal.carbs_g != null) carbs_g += meal.carbs_g;
  }
  return { calories, protein_g, fat_g, carbs_g };
}
