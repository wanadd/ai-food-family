import type { MenuMeal } from "@/lib/menu/types";

/** Public meal heading — prefer catalog display_title over legacy snapshot name. */
export function menuMealHeading(meal: Pick<MenuMeal, "display_title" | "name">): string {
  const display = meal.display_title?.trim();
  if (display) return display;
  return meal.name?.trim() || "";
}
