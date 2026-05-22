import { apiUrl } from "@/lib/api";

import type { AppMode } from "@/lib/app-mode/types";

const RETRYABLE_STATUS = new Set([502, 503, 504]);
const MAX_ATTEMPTS = 3;
const RETRY_DELAY_MS = 1500;

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

function isRetryableStatus(status: number): boolean {
  return RETRYABLE_STATUS.has(status);
}

function formatHttpError(status: number, detail?: string): Error {
  if (isRetryableStatus(status)) {
    return new Error("Сервер временно недоступен. Попробуйте через несколько секунд.");
  }
  return new Error(detail ?? `HTTP ${status}`);
}

async function fetchWithRetry(
  url: string,
  init: RequestInit,
): Promise<Response> {
  let lastError: Error | null = null;

  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt += 1) {
    try {
      const response = await fetch(url, init);

      if (isRetryableStatus(response.status) && attempt < MAX_ATTEMPTS) {
        await sleep(RETRY_DELAY_MS);
        continue;
      }

      return response;
    } catch (err) {
      lastError =
        err instanceof Error ? err : new Error("Не удалось связаться с сервером");
      if (attempt < MAX_ATTEMPTS) {
        await sleep(RETRY_DELAY_MS);
        continue;
      }
    }
  }

  throw (
    lastError ??
    new Error("Сервер временно недоступен. Попробуйте через несколько секунд.")
  );
}

export async function apiFetch<T>(
  initData: string,
  mode: AppMode,
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetchWithRetry(`${apiUrl}${path}`, {
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
    throw formatHttpError(response.status, payload?.detail);
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
  const response = await fetchWithRetry(`${apiUrl}${path}`, {
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
