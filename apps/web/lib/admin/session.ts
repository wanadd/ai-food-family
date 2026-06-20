const STORAGE_KEY = "planam_admin_session";

export function captureAdminSessionFromUrl(): void {
  if (typeof window === "undefined") return;
  const params = new URLSearchParams(window.location.search);
  const token = params.get("admin_session");
  if (!token) return;
  sessionStorage.setItem(STORAGE_KEY, token);
  const url = new URL(window.location.href);
  url.searchParams.delete("admin_session");
  window.history.replaceState({}, "", `${url.pathname}${url.search}`);
}

export function getAdminSessionToken(): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem(STORAGE_KEY);
}

export function clearAdminSessionToken(): void {
  if (typeof window === "undefined") return;
  sessionStorage.removeItem(STORAGE_KEY);
}

export function hasAdminAuthCredential(initData?: string | null): boolean {
  return Boolean(initData || getAdminSessionToken());
}
