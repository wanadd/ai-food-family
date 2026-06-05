"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useLayoutEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { useTelegram } from "@/components/TelegramProvider";
import { isPlanamUi2026Enabled } from "@/lib/planam/feature-flags";
import { applyThemeToDocument } from "@/lib/planam/theme-document";
import { readTelegramWebApp } from "@/lib/telegram-webapp";
import {
  readStoredThemePreference,
  resolveColorScheme,
  writeStoredThemePreference,
  type ThemePreference,
} from "@/lib/planam/theme";

type ThemeContextValue = {
  preference: ThemePreference;
  resolved: "light" | "dark";
  setPreference: (next: ThemePreference) => void;
};

const ThemeContext = createContext<ThemeContextValue | null>(null);

type ThemeProviderProps = {
  children: ReactNode;
  /** When false, does not touch `html` (safe for legacy shell). */
  active?: boolean;
  /** Apply PLANAM 2026 palette scope on `html` (dev preview, onboarding, 2026 shell). */
  scope2026?: boolean;
};

export function ThemeProvider({
  children,
  active = true,
  scope2026 = false,
}: ThemeProviderProps) {
  const { colorScheme: telegramScheme, isTelegram } = useTelegram();
  const [preference, setPreferenceState] = useState<ThemePreference>("system");
  const [systemDark, setSystemDark] = useState(false);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    const stored = readStoredThemePreference();
    if (stored) {
      setPreferenceState(stored);
    }
    setHydrated(true);
  }, []);

  useEffect(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const update = () => setSystemDark(mq.matches);
    update();
    mq.addEventListener("change", update);
    return () => mq.removeEventListener("change", update);
  }, []);

  const resolved = useMemo(() => {
    if (!hydrated) {
      return "light" as const;
    }
    let scheme = resolveColorScheme(preference, systemDark);
    if (
      preference === "system" &&
      isTelegram &&
      (telegramScheme === "dark" || telegramScheme === "light")
    ) {
      scheme = telegramScheme === "dark" ? "dark" : "light";
    }
    return scheme;
  }, [preference, systemDark, hydrated, isTelegram, telegramScheme]);

  const ui2026 = scope2026 || isPlanamUi2026Enabled();

  const telegramHints = useMemo(() => {
    if (!isTelegram || ui2026 || typeof window === "undefined") {
      return null;
    }
    const webApp = readTelegramWebApp();
    const params = webApp?.themeParams;
    if (!params?.bg_color) {
      return null;
    }
    return { bg_color: params.bg_color };
  }, [isTelegram, ui2026]);

  useLayoutEffect(() => {
    if (!hydrated) {
      return undefined;
    }
    return applyThemeToDocument({
      active,
      preference,
      systemDark,
      telegram: telegramHints,
      ui2026: active && ui2026,
    });
  }, [active, preference, systemDark, hydrated, telegramHints, ui2026, scope2026]);

  const setPreference = useCallback((next: ThemePreference) => {
    setPreferenceState(next);
    writeStoredThemePreference(next);
  }, []);

  const value = useMemo(
    () => ({
      preference,
      resolved,
      setPreference,
    }),
    [preference, resolved, setPreference],
  );

  return (
    <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
  );
}

export function usePlanamTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    throw new Error("usePlanamTheme must be used within ThemeProvider");
  }
  return ctx;
}
