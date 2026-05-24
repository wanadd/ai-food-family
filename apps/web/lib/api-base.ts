/** Production API when build env is missing (Telegram Mini App cannot use localhost). */
const PRODUCTION_API_FALLBACK = "https://planam.ru/api";

/**
 * Absolute API base URL for browser fetch (Telegram Mini App requires https, not relative paths).
 */
export function getApiBaseUrl(): string {
  let raw = process.env.NEXT_PUBLIC_API_URL?.trim() ?? "";

  if (typeof window !== "undefined") {
    const host = window.location.hostname;
    const onLocalhost = host === "localhost" || host === "127.0.0.1";
    if ((!raw || raw === "http://localhost:8000") && !onLocalhost) {
      raw = PRODUCTION_API_FALLBACK;
    }
  }

  if (!raw) {
    raw = "http://localhost:8000";
  }

  if (raw.startsWith("/")) {
    if (typeof window !== "undefined") {
      return `${window.location.origin}${raw}`.replace(/\/+$/, "");
    }
    return PRODUCTION_API_FALLBACK;
  }

  if (!/^https?:\/\//i.test(raw)) {
    return `https://${raw.replace(/\/+$/, "")}`;
  }

  return raw.replace(/\/+$/, "");
}

export function buildApiUrl(path: string): string {
  const base = getApiBaseUrl();
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${base}${normalizedPath}`;
}
