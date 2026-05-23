import { apiFetch } from "@/lib/api-client";
import type { AppMode } from "@/lib/app-mode/types";

export type NutritionistAskResponse = {
  answer: string;
  used_ai: boolean;
};

export async function askNutritionist(
  initData: string,
  mode: AppMode,
  message: string,
): Promise<NutritionistAskResponse> {
  return apiFetch<NutritionistAskResponse>(
    initData,
    mode,
    "/nutritionist/ask",
    {
      method: "POST",
      body: JSON.stringify({ message }),
    },
  );
}
