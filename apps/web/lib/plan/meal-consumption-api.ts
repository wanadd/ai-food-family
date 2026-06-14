import { apiFetch, apiGet } from "@/lib/api-client";
import type { AppMode } from "@/lib/app-mode/types";

import type { MealConsumptionStatus } from "./meal-consumption-sheet";

export type MealConsumptionLogEntry = {
  id: number;
  user_id: number | null;
  family_member_id?: number | null;
  meal_type: string | null;
  recipe_id: number | null;
  recipe_title?: string | null;
  status: MealConsumptionStatus | string;
  portion_multiplier: number;
};

export type MealConsumptionBulkPayload = {
  family_id: number;
  menu_selection_id?: number | null;
  day_index?: number | null;
  planned_date?: string | null;
  entries: Array<{
    user_id?: number | null;
    family_member_id?: number | null;
    meal_type: string;
    recipe_id?: number | null;
    recipe_title?: string | null;
    status: MealConsumptionStatus;
    portion_multiplier: number;
  }>;
};

export type MealConsumptionBulkResponse = {
  ok: boolean;
  saved: number;
  entries: MealConsumptionLogEntry[];
};

export type MealConsumptionListResponse = {
  entries: MealConsumptionLogEntry[];
};

export type NutritionTotals = {
  calories: number;
  protein: number;
  fat: number;
  carbs: number;
};

export type MealConsumptionNutritionSummary = {
  mode: "planned" | "actual";
  has_consumption_logs: boolean;
  planned: NutritionTotals;
  actual: NutritionTotals | null;
  counts: {
    planned_meals: number;
    logged_meals: number;
    eaten: number;
    skipped: number;
    ate_out: number;
  };
  targets?: {
    kcal: number | null;
    protein: number | null;
    fat: number | null;
    carbs: number | null;
  } | null;
};

export async function fetchMealConsumptionNutritionSummary(
  initData: string,
  mode: AppMode,
  params: {
    family_id: number;
    menu_selection_id?: number | null;
    day_index?: number | null;
    planned_date?: string | null;
  },
): Promise<MealConsumptionNutritionSummary> {
  const qs = new URLSearchParams();
  qs.set("family_id", String(params.family_id));
  if (params.menu_selection_id != null) {
    qs.set("menu_selection_id", String(params.menu_selection_id));
  }
  if (params.day_index != null) {
    qs.set("day_index", String(params.day_index));
  }
  if (params.planned_date) {
    qs.set("planned_date", params.planned_date);
  }
  const data = await apiGet<MealConsumptionNutritionSummary>(
    initData,
    mode,
    `/meal-consumption/nutrition-summary?${qs.toString()}`,
  );
  if (!data) {
    throw new Error("Не удалось загрузить сводку питания");
  }
  return data;
}

export async function fetchMealConsumptionLogs(
  initData: string,
  mode: AppMode,
  params: {
    family_id: number;
    menu_selection_id?: number | null;
    day_index?: number | null;
    planned_date?: string | null;
  },
): Promise<MealConsumptionLogEntry[]> {
  const qs = new URLSearchParams();
  qs.set("family_id", String(params.family_id));
  if (params.menu_selection_id != null) {
    qs.set("menu_selection_id", String(params.menu_selection_id));
  }
  if (params.day_index != null) {
    qs.set("day_index", String(params.day_index));
  }
  if (params.planned_date) {
    qs.set("planned_date", params.planned_date);
  }
  const data = await apiGet<MealConsumptionListResponse>(
    initData,
    mode,
    `/meal-consumption?${qs.toString()}`,
  );
  return data?.entries ?? [];
}

export async function saveMealConsumptionLogs(
  initData: string,
  mode: AppMode,
  payload: MealConsumptionBulkPayload,
): Promise<MealConsumptionBulkResponse> {
  return apiFetch<MealConsumptionBulkResponse>(
    initData,
    mode,
    "/meal-consumption/bulk",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export const MEAL_CONSUMPTION_SAVE_ERROR =
  "Не удалось сохранить отметки. Попробуйте ещё раз.";

export const MEAL_CONSUMPTION_PERMISSION_ERROR =
  "Нет прав отмечать питание за этого участника";

export const MEAL_CONSUMPTION_FAMILY_REQUIRED_ERROR =
  "Сохранение отметок доступно после настройки семьи";

export function mealConsumptionErrorMessage(err: unknown): string {
  const message =
    err instanceof Error ? err.message : String(err ?? "");
  if (message.includes("Нет прав отмечать")) {
    return MEAL_CONSUMPTION_PERMISSION_ERROR;
  }
  if (message.includes("настройки семьи") || message.includes("настройки семьи")) {
    return MEAL_CONSUMPTION_FAMILY_REQUIRED_ERROR;
  }
  return MEAL_CONSUMPTION_SAVE_ERROR;
}
