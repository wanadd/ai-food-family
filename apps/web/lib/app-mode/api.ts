import { apiUrl } from "@/lib/api";
import { apiFetch } from "@/lib/api-client";

import type { AppContext, AppMode } from "./types";

/**
 * Module-level cache for app-context so that:
 *  - TelegramProvider can kick off the fetch immediately after auth
 *    succeeds (no need to wait for an extra render cycle until
 *    AppModeProvider mounts)
 *  - AppModeProvider re-uses the in-flight or finished result
 *    instead of issuing a duplicate /users/me/app-context request
 *  - Mutations (updateAppMode) refresh the cache so subsequent reads
 *    see the up-to-date mode/family
 */
let inFlight: Promise<AppContext> | null = null;
let cached: { key: string; data: AppContext } | null = null;

function keyFor(initData: string): string {
  return initData.slice(0, 32);
}

export function prefetchAppContext(initData: string): Promise<AppContext> {
  if (!initData) {
    return Promise.reject(new Error("init_data is required"));
  }
  const key = keyFor(initData);
  if (cached?.key === key) {
    return Promise.resolve(cached.data);
  }
  if (inFlight) return inFlight;
  const request = apiFetch<AppContext>(
    initData,
    "personal",
    "/users/me/app-context",
  )
    .then((data) => {
      cached = { key, data };
      return data;
    })
    .finally(() => {
      inFlight = null;
    });
  inFlight = request;
  return request;
}

export async function fetchAppContext(initData: string): Promise<AppContext> {
  return prefetchAppContext(initData);
}

export function invalidateAppContext(): void {
  cached = null;
  inFlight = null;
}

export async function updateAppMode(
  initData: string,
  mode: AppMode,
): Promise<AppContext> {
  const data = await apiFetch<AppContext>(
    initData,
    mode,
    "/users/me/app-context",
    {
      method: "PATCH",
      body: JSON.stringify({ active_mode: mode }),
    },
  );
  cached = { key: keyFor(initData), data };
  return data;
}
