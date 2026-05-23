/** Local dev auth — must match apps/api/app/services/dev_auth.py */

export const DEV_INIT_DATA = "planam-dev-local-v1";

const DEV_INIT_STORAGE_KEY = "planam_dev_init_data";

export function isLocalDevHost(): boolean {
  if (typeof window === "undefined") {
    return false;
  }
  const host = window.location.hostname;
  return host === "localhost" || host === "127.0.0.1";
}

/** True only in `next dev` on localhost (never on production deploy). */
export function isClientDevMode(): boolean {
  return process.env.NODE_ENV === "development" && isLocalDevHost();
}

export function getStoredDevInitData(): string {
  if (typeof window === "undefined" || !isClientDevMode()) {
    return "";
  }
  return sessionStorage.getItem(DEV_INIT_STORAGE_KEY) ?? "";
}

export function storeDevInitData(token: string): void {
  if (typeof window === "undefined" || !isClientDevMode()) {
    return;
  }
  sessionStorage.setItem(DEV_INIT_STORAGE_KEY, token);
}

export function clearDevInitData(): void {
  if (typeof window === "undefined") {
    return;
  }
  sessionStorage.removeItem(DEV_INIT_STORAGE_KEY);
}
