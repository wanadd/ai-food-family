import { apiUrl } from "@/lib/api";

import type { AppMode } from "@/lib/app-mode/types";

export async function apiFetch<T>(
  initData: string,
  mode: AppMode,
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(`${apiUrl}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-Telegram-Init-Data": initData,
      "X-App-Mode": mode,
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as
      | { detail?: string }
      | null;
    throw new Error(payload?.detail ?? `HTTP ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export async function apiGet<T>(
  initData: string,
  mode: AppMode,
  path: string,
): Promise<T | null> {
  const response = await fetch(`${apiUrl}${path}`, {
    headers: {
      "X-Telegram-Init-Data": initData,
      "X-App-Mode": mode,
    },
  });

  if (!response.ok) {
    return null;
  }

  const text = await response.text();
  if (!text || text === "null") {
    return null;
  }

  return JSON.parse(text) as T;
}
