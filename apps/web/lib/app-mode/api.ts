import { apiUrl } from "@/lib/api";
import { apiFetch } from "@/lib/api-client";

import type { AppContext, AppMode } from "./types";

export async function fetchAppContext(initData: string): Promise<AppContext> {
  return apiFetch<AppContext>(initData, "personal", "/users/me/app-context");
}

export async function updateAppMode(
  initData: string,
  mode: AppMode,
): Promise<AppContext> {
  return apiFetch<AppContext>(initData, mode, "/users/me/app-context", {
    method: "PATCH",
    body: JSON.stringify({ active_mode: mode }),
  });
}
