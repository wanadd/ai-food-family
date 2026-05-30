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
