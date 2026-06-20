/**
 * PLANAM 2026 theme preference (Light / Dark / System).
 * @see docs/PLANAM_DESIGN_SYSTEM_2026.md §1.4
 */

export type ThemePreference = "light" | "dark" | "system";

export const THEME_STORAGE_KEY = "planam-2026-theme";

export function isThemePreference(value: string): value is ThemePreference {
  return value === "light" || value === "dark" || value === "system";
}

export function readStoredThemePreference(): ThemePreference | null {
  if (typeof window === "undefined") {
    return null;
  }
  try {
    const raw = window.localStorage.getItem(THEME_STORAGE_KEY);
    if (raw && isThemePreference(raw)) {
      return raw;
    }
  } catch {
    /* private mode / blocked storage */
  }
  return null;
}

export function writeStoredThemePreference(preference: ThemePreference): void {
  if (typeof window === "undefined") {
    return;
  }
  try {
    window.localStorage.setItem(THEME_STORAGE_KEY, preference);
  } catch {
    /* ignore */
  }
}

export function resolveColorScheme(
  preference: ThemePreference,
  systemDark: boolean,
): "light" | "dark" {
  if (preference === "system") {
    return systemDark ? "dark" : "light";
  }
  return preference;
}

export function isPlanamDevPreviewPath(pathname: string | null): boolean {
  return Boolean(pathname?.startsWith("/dev/planam-2026"));
}
