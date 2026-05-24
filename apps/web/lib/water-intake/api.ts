import { apiFetch, apiGet } from "@/lib/api-client";
import type { AppMode } from "@/lib/app-mode/types";

export type WaterToday = {
  total_ml: number;
  target_ml: number | null;
};

export async function fetchWaterToday(
  initData: string,
  mode: AppMode,
): Promise<WaterToday> {
  const data = await apiGet<WaterToday>(initData, mode, "/nutritionist/water/today");
  return data ?? { total_ml: 0, target_ml: null };
}

export async function addWaterIntake(
  initData: string,
  mode: AppMode,
  amountMl: number,
): Promise<WaterToday> {
  return apiFetch(initData, mode, "/nutritionist/water", {
    method: "POST",
    body: JSON.stringify({ amount_ml: amountMl }),
  });
}
