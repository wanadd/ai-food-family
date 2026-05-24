import {
  ALLERGY_OPTIONS,
  BUDGET_OPTIONS,
  COOKING_TIME_OPTIONS,
  DIET_OPTIONS,
} from "@/lib/nutrition-profile/options";
import type { NutritionProfileData } from "@/lib/nutrition-profile/types";
import type { PantryList } from "@/lib/pantry/types";

function labels(
  values: string[],
  options: { value: string; label: string }[],
): string {
  if (!values.length) return "";
  return values
    .filter((v) => v !== "none")
    .map((v) => options.find((o) => o.value === v)?.label ?? v)
    .join(", ");
}

export function buildRestrictionsSummary(
  profile: NutritionProfileData | null,
): {
  allergies: string;
  diets: string;
  disliked: string;
  medical: string;
} {
  if (!profile) {
    return {
      allergies: "Не указано",
      diets: "Не указано",
      disliked: "Не указано",
      medical: "Не указано",
    };
  }
  return {
    allergies: labels(profile.allergies, ALLERGY_OPTIONS) || "Нет",
    diets: labels(profile.diets, DIET_OPTIONS) || "Без особенностей",
    disliked: profile.disliked_foods.trim() || profile.banned_foods.trim() || "Нет",
    medical: profile.medical_restrictions.trim() || "Нет",
  };
}

export type ChecklistItemStatus = "included" | "missing" | "add";

export function buildChecklistItemStatuses(
  profile: NutritionProfileData | null,
  personsCount: number,
  pantry: PantryList | null,
  isFamily: boolean,
): Record<string, ChecklistItemStatus> {
  const state = buildChecklistState(profile, personsCount, pantry);
  return {
    profile: state.profile ? "included" : "add",
    persons: isFamily ? (state.persons ? "included" : "missing") : "included",
    pantry: state.pantry ? "included" : "add",
    leftovers: state.leftovers ? "included" : "add",
    allergies: state.allergies ? "included" : "add",
    budget: state.budget ? "included" : "add",
    cooking_time: state.cooking_time ? "included" : "add",
  };
}

export function buildChecklistState(
  profile: NutritionProfileData | null,
  personsCount: number,
  pantry: PantryList | null,
): Record<string, boolean> {
  const hasProfile = Boolean(profile?.nutrition_goal);
  const hasPantry = (pantry?.active_count ?? 0) > 0;
  const hasLeftovers = pantry?.items.some(
    (i) => i.source === "manual" && (i.note?.includes("остат") || false),
  );
  return {
    profile: hasProfile,
    persons: personsCount >= 1,
    pantry: hasPantry,
    leftovers: hasLeftovers ?? hasPantry,
    allergies: Boolean(
      profile?.allergies?.filter((a) => a !== "none").length,
    ),
    budget: Boolean(profile?.budget),
    cooking_time: Boolean(profile?.cooking_time),
  };
}

export function formatGoalLabel(goalId: string | null): string {
  const map: Record<string, string> = {
    maintain: "Поддержание веса",
    lose: "Похудение",
    gain: "Набор массы",
    healthy: "Здоровое питание",
    sport: "Спорт",
    kids: "Детское питание",
  };
  if (!goalId) return "Не задана";
  return map[goalId] ?? goalId;
}
