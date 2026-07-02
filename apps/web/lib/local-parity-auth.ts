/** Local prod-parity auth gate. Requires explicit public flag and localhost. */

const LOCAL_PARITY_INIT_STORAGE_KEY = "planam_local_parity_init_data";

export function isLocalParityHost(): boolean {
  if (typeof window === "undefined") {
    return false;
  }
  const host = window.location.hostname;
  return host === "localhost" || host === "127.0.0.1";
}

export function isLocalParityModeEnabled(): boolean {
  return (
    process.env.NEXT_PUBLIC_LOCAL_PARITY_MODE === "true" &&
    isLocalParityHost()
  );
}

export function getStoredLocalParityInitData(): string {
  if (typeof window === "undefined" || !isLocalParityModeEnabled()) {
    return "";
  }
  return sessionStorage.getItem(LOCAL_PARITY_INIT_STORAGE_KEY) ?? "";
}

export function storeLocalParityInitData(token: string): void {
  if (typeof window === "undefined" || !isLocalParityModeEnabled()) {
    return;
  }
  sessionStorage.setItem(LOCAL_PARITY_INIT_STORAGE_KEY, token);
}

export function clearLocalParityInitData(): void {
  if (typeof window === "undefined") {
    return;
  }
  sessionStorage.removeItem(LOCAL_PARITY_INIT_STORAGE_KEY);
}
