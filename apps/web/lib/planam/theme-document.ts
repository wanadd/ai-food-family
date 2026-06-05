import type { ThemePreference } from "@/lib/planam/theme";
import { resolveColorScheme } from "@/lib/planam/theme";
import {
  applyPlanamUi2026Scope,
  clearPlanamUi2026Scope,
} from "@/lib/planam/ui-scope";

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
  /** When true, keep PLANAM DS colors (no Telegram canvas override). */
  ui2026?: boolean;
}): () => void {
  if (!options.active || typeof document === "undefined") {
    return () => undefined;
  }

  const root = document.documentElement;
  const resolved = resolveColorScheme(options.preference, options.systemDark);
  const ui2026 = Boolean(options.ui2026);

  root.classList.toggle("dark", resolved === "dark");
  root.dataset.planamTheme = resolved;
  root.dataset.planamThemePreference = options.preference;
  if (ui2026) {
    applyPlanamUi2026Scope(root);
  } else {
    clearPlanamUi2026Scope(root);
  }
  if (resolved === "dark") {
    root.style.colorScheme = "dark";
  } else {
    root.style.colorScheme = "light";
  }

  const prevCanvas = root.style.getPropertyValue("--pa-bg-canvas");
  const prevSurface = root.style.getPropertyValue("--pa-bg-surface");

  const tg = options.telegram;
  if (!ui2026 && tg?.bg_color) {
    root.style.setProperty("--pa-bg-canvas", tg.bg_color);
  } else {
    root.style.removeProperty("--pa-bg-canvas");
  }
  if (!ui2026 && tg?.secondary_bg_color) {
    root.style.setProperty("--pa-bg-surface", tg.secondary_bg_color);
  } else if (!ui2026 && !tg?.bg_color) {
    root.style.removeProperty("--pa-bg-surface");
  } else if (ui2026) {
    root.style.removeProperty("--pa-bg-surface");
  }

  return () => {
    root.classList.remove("dark");
    root.style.colorScheme = "";
    delete root.dataset.planamTheme;
    delete root.dataset.planamThemePreference;
    clearPlanamUi2026Scope(root);
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
