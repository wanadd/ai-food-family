import { getNutritionSectionChecks } from "@/lib/nutrition-profile/sections";
import { NUTRITION_GOAL_LABELS } from "@/lib/nutrition-profile/options";
import type { NutritionProfileData } from "@/lib/nutrition-profile/types";

export function isNutritionProfileComplete(
  data: NutritionProfileData | null,
): boolean {
  if (!data) return false;
  const { filled, total } = getNutritionSectionChecks(data);
  return data.completed || filled >= total - 1;
}

export function getNutritionGoalLabel(
  data: NutritionProfileData | null,
): string | null {
  if (!data?.nutrition_goal) return null;
  return NUTRITION_GOAL_LABELS[data.nutrition_goal] ?? null;
}

export function getNutritionProfileProgress(
  data: NutritionProfileData | null,
): number {
  if (!data) return 0;
  return getNutritionSectionChecks(data).percent;
}

export { getNutritionSectionChecks };
