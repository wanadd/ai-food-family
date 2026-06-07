import { buildApiUrl } from "@/lib/api-base";
import { apiFetch, apiGet, formatNetworkError } from "@/lib/api-client";
import { ApiRequestError } from "@/lib/api-errors";
import type { AppMode } from "@/lib/app-mode/types";

import {
  buildMenuGeneratePayload,
  menuGenerateDebugMeta,
  type BuildGeneratePayloadInput,
} from "./generate-payload";
import type {
  MenuGenerateResponse,
  MenuVariant,
  SelectedMenu,
} from "./types";

export type MenuGenerateOptions = {
  persons_count?: number;
  plan_mode?: string;
  plan_days?: number;
  nutrition_goal?: string;
};

const MENU_GENERATE_PATH = "/menus/generate";

function menuGenDevLog(
  event: "menu generate request started" | "menu generate request failed" | "menu generate response received",
  meta?: Record<string, unknown>,
): void {
  if (process.env.NODE_ENV === "development") {
    console.info(`[PlanAm] ${event}`, meta ?? "");
  }
}

export async function generateMenus(
  initData: string,
  mode: AppMode,
  input: BuildGeneratePayloadInput,
): Promise<MenuGenerateResponse> {
  if (!initData?.trim()) {
    throw new Error("Нет данных авторизации Telegram. Перезапустите Mini App.");
  }

  const payload = buildMenuGeneratePayload(input);
  const url = buildApiUrl(MENU_GENERATE_PATH);

  menuGenDevLog("menu generate request started", menuGenerateDebugMeta(input, url));

  try {
    const result = await apiFetch<MenuGenerateResponse>(
      initData,
      mode,
      MENU_GENERATE_PATH,
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    );
    menuGenDevLog("menu generate response received", {
      variants: result.menus?.length ?? 0,
    });
    return result;
  } catch (err) {
    menuGenDevLog("menu generate request failed", {
      message: err instanceof Error ? err.message : String(err),
      url,
    });
    if (err instanceof ApiRequestError) {
      throw err;
    }
    throw formatNetworkError(
      err,
      "Не удалось создать меню. Попробуйте ещё раз.",
    );
  }
}

export async function replaceDish(
  initData: string,
  mode: AppMode,
  menu: MenuVariant,
  mealIndex: number,
  hint?: string,
  dayIndex?: number,
): Promise<MenuVariant> {
  return apiFetch<MenuVariant>(initData, mode, "/menus/replace-dish", {
    method: "POST",
    body: JSON.stringify({
      menu,
      meal_index: mealIndex,
      day_index: dayIndex ?? null,
      hint: hint || null,
    }),
  });
}

export async function selectMenu(
  initData: string,
  mode: AppMode,
  menu: MenuVariant,
): Promise<SelectedMenu> {
  return apiFetch<SelectedMenu>(initData, mode, "/menus/select", {
    method: "POST",
    body: JSON.stringify({ menu }),
  });
}

export async function fetchSelectedMenu(
  initData: string,
  mode: AppMode,
): Promise<SelectedMenu | null> {
  return apiGet<SelectedMenu>(initData, mode, "/menus/selected");
}

export type MenuPlanItem = {
  slot_id: string;
  date: string;
  meal_type: string;
  recipe_id: number | null;
  name: string;
  servings: number;
  prep_time_minutes: number;
  calories_estimate?: number | null;
};

export type MenuTodayResponse = {
  date: string;
  items: MenuPlanItem[];
  menu: MenuVariant | null;
};

export async function fetchMenuToday(
  initData: string,
  mode: AppMode,
  date?: string,
): Promise<MenuTodayResponse> {
  const query = date ? `?date=${encodeURIComponent(date)}` : "";
  const data = await apiGet<MenuTodayResponse>(initData, mode, `/menus/today${query}`);
  if (!data) {
    return { date: date ?? new Date().toISOString().slice(0, 10), items: [], menu: null };
  }
  return data;
}

export async function deleteMenuItem(
  initData: string,
  mode: AppMode,
  slotId: string,
): Promise<SelectedMenu> {
  const encoded = encodeURIComponent(slotId);
  const data = await apiFetch<SelectedMenu>(
    initData,
    mode,
    `/menus/items/${encoded}`,
    { method: "DELETE" },
  );
  if (!data) {
    throw new Error("Не удалось удалить блюдо из меню");
  }
  return data;
}

export type ReplaceMenuSlotResponse = {
  item: MenuPlanItem;
  menu: MenuVariant;
};

export type NutritionConfidence =
  | "exact"
  | "estimated"
  | "low_confidence"
  | "unavailable";

export type NutritionMacros = {
  kcal: number;
  protein: number;
  fat: number;
  carbs: number;
};

export type DayNutrition = {
  date: string;
  totals: NutritionMacros;
  targets: {
    kcal: number | null;
    protein: number | null;
    fat: number | null;
    carbs: number | null;
  };
  progress: {
    kcal_pct: number | null;
    protein_pct: number | null;
    fat_pct: number | null;
    carbs_pct: number | null;
  };
  confidence: NutritionConfidence;
  coverage: {
    total_items: number;
    calculated_items: number;
    exact_items: number;
    estimated_items: number;
    low_confidence_items: number;
    unavailable_items: number;
    coverage_pct: number;
  };
  meals: Array<{
    meal_type: string;
    totals: NutritionMacros;
    items: Array<{
      recipe_id: number | null;
      name: string;
      kcal: number | null;
      confidence: NutritionConfidence | null;
    }>;
  }>;
  warnings: string[];
};

export type WeekNutrition = {
  start_date: string;
  end_date: string;
  days: DayNutrition[];
  weekly_total: NutritionMacros;
  weekly_average: NutritionMacros;
  days_with_full_calc: number;
  confidence: NutritionConfidence;
  warnings: string[];
};

export async function fetchMenuDayNutrition(
  initData: string,
  mode: AppMode,
  date?: string,
): Promise<DayNutrition | null> {
  const query = date ? `?date=${encodeURIComponent(date)}` : "";
  return apiGet<DayNutrition>(initData, mode, `/menus/nutrition${query}`);
}

export async function fetchMenuWeekNutrition(
  initData: string,
  mode: AppMode,
  start?: string,
): Promise<WeekNutrition | null> {
  const query = start ? `?start=${encodeURIComponent(start)}` : "";
  return apiGet<WeekNutrition>(initData, mode, `/menus/nutrition/week${query}`);
}

export async function replaceMenuSlot(
  initData: string,
  mode: AppMode,
  slotId: string,
  recipeId: number,
  servings?: number,
): Promise<ReplaceMenuSlotResponse> {
  const encoded = encodeURIComponent(slotId);
  const data = await apiFetch<ReplaceMenuSlotResponse>(
    initData,
    mode,
    `/menus/items/${encoded}/replace`,
    {
      method: "POST",
      body: JSON.stringify({
        recipe_id: recipeId,
        servings: servings ?? null,
      }),
    },
  );
  if (!data) {
    throw new Error("Не удалось заменить блюдо");
  }
  return data;
}
