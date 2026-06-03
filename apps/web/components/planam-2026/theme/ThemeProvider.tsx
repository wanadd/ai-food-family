"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { useTelegram } from "@/components/TelegramProvider";
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
};

export function ThemeProvider({ children, active = true }: ThemeProviderProps) {
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

  const telegramHints = useMemo(() => {
    if (!isTelegram || typeof window === "undefined") {
      return null;
    }
    const webApp = readTelegramWebApp();
    const params = webApp?.themeParams;
    if (!params?.bg_color) {
      return null;
    }
    return { bg_color: params.bg_color };
  }, [isTelegram]);

  useEffect(() => {
    if (!hydrated) {
      return undefined;
    }
    return applyThemeToDocument({
      active,
      preference,
      systemDark,
      telegram: telegramHints,
    });
  }, [active, preference, systemDark, hydrated, telegramHints, resolved]);

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
