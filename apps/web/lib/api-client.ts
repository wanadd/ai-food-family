import { buildApiUrl } from "@/lib/api-base";
import { ApiRequestError, parseApiErrorDetail } from "@/lib/api-errors";

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

function isNetworkFetchError(err: unknown): boolean {
  if (!(err instanceof Error)) return false;
  const msg = err.message.toLowerCase();
  return (
    err.name === "TypeError" ||
    msg.includes("failed to fetch") ||
    msg.includes("networkerror") ||
    msg.includes("load failed")
  );
}

export function formatNetworkError(
  err: unknown,
  fallback = "Не удалось связаться с сервером",
): Error {
  if (isNetworkFetchError(err)) {
    return new Error(fallback);
  }
  if (err instanceof Error) {
    return err;
  }
  return new Error(fallback);
}

function formatHttpError(status: number, detail?: unknown): Error {
  if (isRetryableStatus(status)) {
    return new Error("Сервер временно недоступен. Попробуйте через несколько секунд.");
  }
  const parsed = parseApiErrorDetail(detail);
  if (parsed?.message) {
    return new ApiRequestError(parsed.message, parsed);
  }
  if (typeof detail === "string") {
    return new Error(detail);
  }
  return new Error(`HTTP ${status}`);
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
      lastError = formatNetworkError(
        err,
        "Сервер временно недоступен. Попробуйте через несколько секунд.",
      );
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
  const response = await fetchWithRetry(buildApiUrl(path), {
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
      | { detail?: unknown }
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
  const response = await fetchWithRetry(buildApiUrl(path), {
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
