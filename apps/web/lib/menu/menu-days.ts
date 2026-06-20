import type { MenuDayPlan, MenuMeal, MenuVariant } from "./types";

export function menuHasMultipleDays(menu: MenuVariant): boolean {
  return Boolean(menu.days && menu.days.length > 1);
}

export function getMenuDays(menu: MenuVariant): MenuDayPlan[] {
  if (menu.days?.length) {
    return menu.days;
  }
  return [
    {
      day_index: 1,
      label: "Сегодня",
      date_iso: new Date().toISOString().slice(0, 10),
      meals: menu.meals,
    },
  ];
}

export function mealsForDayIndex(menu: MenuVariant, dayIndex: number): MenuMeal[] {
  const days = getMenuDays(menu);
  const day = days.find((d) => d.day_index === dayIndex) ?? days[0];
  return day?.meals ?? menu.meals;
}

export function dateIsoForDayIndex(menu: MenuVariant, dayIndex: number): string {
  const days = getMenuDays(menu);
  const day = days.find((d) => d.day_index === dayIndex) ?? days[0];
  return day?.date_iso ?? new Date().toISOString().slice(0, 10);
}

export function defaultDayIndex(menu: MenuVariant): number {
  const today = new Date().toISOString().slice(0, 10);
  const days = getMenuDays(menu);
  const match = days.find((d) => d.date_iso === today);
  return match?.day_index ?? days[0]?.day_index ?? 1;
}

export function menuViewForDay(menu: MenuVariant, dayIndex: number): MenuVariant {
  const meals = mealsForDayIndex(menu, dayIndex);
  return { ...menu, meals };
}

/** Merge replace-dish API result back into the full multi-day menu. */
export function mergeReplaceResult(
  fullMenu: MenuVariant,
  replaceResult: MenuVariant,
  dayIndex: number,
): MenuVariant {
  if (!fullMenu.days?.length) {
    return replaceResult;
  }

  const replacedDayMeals = replaceResult.meals;
  const days = fullMenu.days.map((day) =>
    day.day_index === dayIndex ? { ...day, meals: replacedDayMeals } : day,
  );

  return {
    ...fullMenu,
    title: replaceResult.title,
    tagline: replaceResult.tagline,
    explanation: replaceResult.explanation,
    estimated_daily_cost: replaceResult.estimated_daily_cost,
    total_prep_minutes: replaceResult.total_prep_minutes,
    ingredients:
      replaceResult.ingredients.length > 0
        ? replaceResult.ingredients
        : fullMenu.ingredients,
    days,
    meals: days[0]?.meals ?? fullMenu.meals,
    plan_days: fullMenu.plan_days,
    variant: replaceResult.variant,
  };
}
