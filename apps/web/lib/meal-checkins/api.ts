import { apiFetch, apiGet } from "@/lib/api-client";
import type { AppMode } from "@/lib/app-mode/types";

import type { MealCheckinStatus } from "./constants";

export type MealCheckin = {
  id: number;
  meal_type: string;
  planned_date: string;
  actual_status: string;
  actual_description: string | null;
  leftover_servings_delta: number | null;
  family_member_id?: number | null;
  member_name?: string | null;
  created_at: string;
};

export async function fetchTodayMealCheckins(
  initData: string,
  mode: AppMode,
  onDate?: string,
): Promise<MealCheckin[]> {
  const qs = onDate ? `?on_date=${encodeURIComponent(onDate)}` : "";
  const data = await apiGet<MealCheckin[]>(
    initData,
    mode,
    `/meal-checkins/today${qs}`,
  );
  return data ?? [];
}

export async function createMealCheckin(
  initData: string,
  mode: AppMode,
  payload: {
    meal_type: string;
    actual_status: MealCheckinStatus | "saved_as_leftover";
    planned_date?: string;
    family_member_id?: number | null;
    actual_description?: string | null;
    recipe_id?: number;
    leftover_servings_delta?: number | null;
    leftover_status?: string | null;
  },
): Promise<MealCheckin> {
  return apiFetch(initData, mode, "/meal-checkins", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
