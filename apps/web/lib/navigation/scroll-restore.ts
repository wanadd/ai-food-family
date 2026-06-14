const STORAGE_PREFIX = "planam:scroll:";

function storageKey(pathname: string, query: string): string {
  return `${STORAGE_PREFIX}${pathname}?${query}`;
}

export function saveScrollPosition(
  pathname: string,
  query: string,
  y: number,
): void {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.setItem(storageKey(pathname, query), String(Math.round(y)));
  } catch {
    /* ignore quota */
  }
}

export function readScrollPosition(pathname: string, query: string): number | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = sessionStorage.getItem(storageKey(pathname, query));
    if (!raw) return null;
    const y = Number(raw);
    return Number.isFinite(y) ? y : null;
  } catch {
    return null;
  }
}

export function clearScrollPosition(pathname: string, query: string): void {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.removeItem(storageKey(pathname, query));
  } catch {
    /* ignore */
  }
}

export function restoreScrollPosition(
  pathname: string,
  query: string,
  behavior: ScrollBehavior = "auto",
): boolean {
  const y = readScrollPosition(pathname, query);
  if (y == null) return false;
  window.scrollTo({ top: y, behavior });
  clearScrollPosition(pathname, query);
  return true;
}
