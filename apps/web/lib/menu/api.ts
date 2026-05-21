import { apiFetch, apiGet } from "@/lib/api-client";
import type { AppMode } from "@/lib/app-mode/types";

import type {
  MenuGenerateResponse,
  MenuVariant,
  SelectedMenu,
} from "./types";

export async function generateMenus(
  initData: string,
  mode: AppMode,
): Promise<MenuGenerateResponse> {
  return apiFetch<MenuGenerateResponse>(initData, mode, "/menus/generate", {
    method: "POST",
  });
}

export async function replaceDish(
  initData: string,
  mode: AppMode,
  menu: MenuVariant,
  mealIndex: number,
  hint?: string,
): Promise<MenuVariant> {
  return apiFetch<MenuVariant>(initData, mode, "/menus/replace-dish", {
    method: "POST",
    body: JSON.stringify({ menu, meal_index: mealIndex, hint: hint || null }),
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
