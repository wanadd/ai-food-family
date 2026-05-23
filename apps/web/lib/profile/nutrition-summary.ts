import { NUTRITION_GOAL_LABELS } from "@/lib/nutrition-profile/options";
import type { NutritionProfileData } from "@/lib/nutrition-profile/types";

export function isNutritionProfileComplete(
  data: NutritionProfileData | null,
): boolean {
  return Boolean(data?.completed && data.nutrition_goal);
}

export function getNutritionGoalLabel(
  data: NutritionProfileData | null,
): string | null {
  if (!data?.nutrition_goal) {
    return null;
  }
  return NUTRITION_GOAL_LABELS[data.nutrition_goal] ?? null;
}

export function getNutritionProfileProgress(
  data: NutritionProfileData | null,
): number {
  if (!data) {
    return 0;
  }
  if (data.completed) {
    return 100;
  }
  let filled = 0;
  if (data.nutrition_goal) filled += 1;
  if (data.activity_level) filled += 1;
  if (data.age) filled += 1;
  if (data.allergies.length || data.diets.length) filled += 1;
  if (data.budget && data.cooking_time) filled += 1;
  return Math.min(90, filled * 18);
}
