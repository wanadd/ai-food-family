import { apiFetch, apiGet } from "@/lib/api-client";
import type { AppMode } from "@/lib/app-mode/types";

export type MealLeftover = {
  id: number;
  scope_mode: string;
  dish_name: string;
  portions_remaining: number;
  valid_until: string | null;
  note: string | null;
  leftover_status: string;
  created_at: string;
  updated_at: string;
};

export async function fetchMealLeftovers(
  initData: string,
  mode: AppMode,
): Promise<MealLeftover[]> {
  const data = await apiGet<MealLeftover[]>(initData, mode, "/meal-leftovers");
  return data ?? [];
}

export async function createMealLeftover(
  initData: string,
  mode: AppMode,
  payload: {
    dish_name: string;
    portions_remaining: number;
    valid_until?: string | null;
    note?: string | null;
  },
): Promise<MealLeftover> {
  return apiFetch(initData, mode, "/meal-leftovers", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateMealLeftover(
  initData: string,
  mode: AppMode,
  id: number,
  payload: {
    portions_remaining?: number;
    leftover_status?: string;
  },
): Promise<MealLeftover> {
  return apiFetch(initData, mode, `/meal-leftovers/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deleteMealLeftover(
  initData: string,
  mode: AppMode,
  id: number,
): Promise<void> {
  await apiFetch(initData, mode, `/meal-leftovers/${id}`, { method: "DELETE" });
}
