import type { ThemePreference } from "@/lib/planam/theme";
import { resolveColorScheme } from "@/lib/planam/theme";

export type TelegramThemeHints = {
  bg_color?: string;
  secondary_bg_color?: string;
};

/**
 * Apply resolved light/dark to `html` and optional Telegram canvas overrides.
 * Only mutates document when `active` is true (legacy UI stays untouched).
 */
export function applyThemeToDocument(options: {
  active: boolean;
  preference: ThemePreference;
  systemDark: boolean;
  telegram?: TelegramThemeHints | null;
}): () => void {
  if (!options.active || typeof document === "undefined") {
    return () => undefined;
  }

  const root = document.documentElement;
  const resolved = resolveColorScheme(options.preference, options.systemDark);

  root.classList.toggle("dark", resolved === "dark");
  root.dataset.planamTheme = resolved;
  root.dataset.planamThemePreference = options.preference;

  const prevCanvas = root.style.getPropertyValue("--pa-bg-canvas");
  const prevSurface = root.style.getPropertyValue("--pa-bg-surface");

  const tg = options.telegram;
  if (tg?.bg_color) {
    root.style.setProperty("--pa-bg-canvas", tg.bg_color);
  } else {
    root.style.removeProperty("--pa-bg-canvas");
  }
  if (tg?.secondary_bg_color) {
    root.style.setProperty("--pa-bg-surface", tg.secondary_bg_color);
  } else if (!tg?.bg_color) {
    root.style.removeProperty("--pa-bg-surface");
  }

  return () => {
    root.classList.remove("dark");
    delete root.dataset.planamTheme;
    delete root.dataset.planamThemePreference;
    if (prevCanvas) {
      root.style.setProperty("--pa-bg-canvas", prevCanvas);
    } else {
      root.style.removeProperty("--pa-bg-canvas");
    }
    if (prevSurface) {
      root.style.setProperty("--pa-bg-surface", prevSurface);
    } else {
      root.style.removeProperty("--pa-bg-surface");
    }
  };
}
