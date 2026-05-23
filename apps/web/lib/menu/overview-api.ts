import { apiFetch, apiGet } from "@/lib/api-client";
import type { AppMode } from "@/lib/app-mode/types";

import type { MenuOverview } from "./overview-types";

export type QuickActionId =
  | "cheaper"
  | "more_pantry"
  | "more_protein"
  | "less_cooking_time"
  | "replace_dish";

export async function fetchMenuOverview(
  initData: string,
  mode: AppMode,
): Promise<MenuOverview> {
  const data = await apiGet<MenuOverview>(initData, mode, "/menus/overview");
  if (!data) throw new Error("Не удалось загрузить меню");
  return data;
}

export async function runMenuQuickAction(
  initData: string,
  mode: AppMode,
  action: QuickActionId,
): Promise<{
  action: string;
  redirect_path: string | null;
  selected_menu: MenuOverview["selected_menu"];
  message: string | null;
}> {
  return apiFetch(initData, mode, "/menus/quick-action", {
    method: "POST",
    body: JSON.stringify({ action }),
  });
}
