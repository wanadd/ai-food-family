import { buildApiUrl } from "@/lib/api-base";
import { ApiRequestError, parseApiErrorDetail } from "@/lib/api-errors";
import { buildProtectedRequestHeaders } from "@/lib/audit/audit-mode";

import type { AppMode } from "@/lib/app-mode/types";

const RETRYABLE_STATUS = new Set([502, 503, 504]);

/**
 * GET fetches sit on the startup critical path (auth → app-context →
 * home data fetches) so we keep the retry budget short to avoid hiding
 * multiple seconds of latency. A single 300ms retry catches transient
 * gateway errors without blocking the user noticeably.
 */
const MAX_ATTEMPTS_GET = 2;
const RETRY_DELAY_GET_MS = 300;

/**
 * Mutations are less frequent and the user usually sees a busy state,
 * so we can afford a slightly longer retry to ride out cold backends
 * or short nginx blips.
 */
const MAX_ATTEMPTS_MUTATION = 2;
const RETRY_DELAY_MUTATION_MS = 800;

function retryProfile(method: string | undefined): {
  maxAttempts: number;
  delayMs: number;
} {
  const upper = (method ?? "GET").toUpperCase();
  if (upper === "GET" || upper === "HEAD") {
    return { maxAttempts: MAX_ATTEMPTS_GET, delayMs: RETRY_DELAY_GET_MS };
  }
  return {
    maxAttempts: MAX_ATTEMPTS_MUTATION,
    delayMs: RETRY_DELAY_MUTATION_MS,
  };
}

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
  const { maxAttempts, delayMs } = retryProfile(init.method);
  let lastError: Error | null = null;

  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    try {
      const response = await fetch(url, init);

      if (isRetryableStatus(response.status) && attempt < maxAttempts) {
        await sleep(delayMs);
        continue;
      }

      return response;
    } catch (err) {
      lastError = formatNetworkError(
        err,
        "Сервер временно недоступен. Попробуйте через несколько секунд.",
      );
      if (attempt < maxAttempts) {
        await sleep(delayMs);
        continue;
      }
    }
  }

  throw (
    lastError ??
    new Error("Сервер временно недоступен. Попробуйте через несколько секунд.")
  );
}

function authHeaders(initData: string, mode: AppMode): Record<string, string> {
  return {
    "Content-Type": "application/json",
    ...buildProtectedRequestHeaders(initData, mode),
  };
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
      ...authHeaders(initData, mode),
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const errText = await response.text().catch(() => "");
    let detail: unknown;
    if (errText.trim()) {
      try {
        detail = (JSON.parse(errText) as { detail?: unknown }).detail;
      } catch {
        detail = errText;
      }
    }
    throw formatHttpError(response.status, detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const text = await response.text();
  if (!text.trim() || text.trim() === "null") {
    return undefined as T;
  }

  try {
    return JSON.parse(text) as T;
  } catch {
    throw new Error("Некорректный ответ сервера");
  }
}

export async function apiGet<T>(
  initData: string,
  mode: AppMode,
  path: string,
): Promise<T | null> {
  const response = await fetchWithRetry(buildApiUrl(path), {
    headers: authHeaders(initData, mode),
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
