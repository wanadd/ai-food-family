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

import {
  authenticateDevLogin,
  authenticateWithTelegram,
  type AuthUser,
} from "@/lib/api";
import { prefetchAppContext } from "@/lib/app-mode/api";
import { isClientDevMode, storeDevInitData } from "@/lib/dev-auth";
import { isPlanamUi2026Enabled } from "@/lib/planam/feature-flags";
import { loadTelegramWebApp } from "@/lib/telegram-webapp";

type TelegramContextValue = {
  isTelegram: boolean;
  isDevMode: boolean;
  initData: string;
  platform: string;
  colorScheme: string;
  user: AuthUser | null;
  isNewUser: boolean;
  isAuthenticating: boolean;
  authError: string | null;
  retryAuth: () => void;
};

const TelegramContext = createContext<TelegramContextValue | null>(null);

const defaultContext: TelegramContextValue = {
  isTelegram: false,
  isDevMode: false,
  initData: "",
  platform: "unknown",
  colorScheme: "light",
  user: null,
  isNewUser: false,
  isAuthenticating: false,
  authError: null,
  retryAuth: () => {},
};

const isDev =
  typeof process !== "undefined" && process.env?.NODE_ENV !== "production";

function debugAuthLog(message: string, extra?: Record<string, unknown>) {
  if (!isDev) return;
  if (typeof console === "undefined") return;
  if (extra) console.info(`[PlanAm/Auth] ${message}`, extra);
  else console.info(`[PlanAm/Auth] ${message}`);
}

export function TelegramProvider({ children }: { children: ReactNode }) {
  const [mounted, setMounted] = useState(false);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isNewUser, setIsNewUser] = useState(false);
  const [isAuthenticating, setIsAuthenticating] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const [authAttempt, setAuthAttempt] = useState(0);
  const [initData, setInitData] = useState("");
  const [isTelegram, setIsTelegram] = useState(false);
  const [isDevMode, setIsDevMode] = useState(false);
  const [platform, setPlatform] = useState("unknown");
  const [colorScheme, setColorScheme] = useState("light");

  useEffect(() => {
    setMounted(true);
  }, []);

  const runAuth = useCallback(async () => {
    // Step 1: actually wait for Telegram.WebApp before deciding whether
    // we're in Telegram or in dev. The previous version read the global
    // synchronously and could see an empty initData if the client
    // injected the global a tick later — that produced the auth-loop
    // ("Open in Telegram" → share phone → still no initData → repeat).
    setIsAuthenticating(true);
    setAuthError(null);

    const webApp = await loadTelegramWebApp();
    const telegramInitData = webApp?.initData ?? "";

    debugAuthLog("loadTelegramWebApp resolved", {
      hasWebApp: Boolean(webApp),
      hasInitData: telegramInitData.length > 0,
      platform: webApp?.platform,
    });

    if (webApp) {
      try {
        webApp.ready();
        webApp.expand();
      } catch {
        /* old clients may not implement these — safe to ignore */
      }
      setPlatform(webApp.platform || "unknown");
      setColorScheme(webApp.colorScheme || "light");
      if (typeof document !== "undefined") {
        const fallbackBg = isPlanamUi2026Enabled() ? "#FFFFFF" : "#f8fafc";
        document.documentElement.style.setProperty(
          "--tg-theme-bg-color",
          webApp.themeParams?.bg_color ?? fallbackBg,
        );
      }
    }

    if (telegramInitData.length > 0) {
      try {
        const result = await authenticateWithTelegram(telegramInitData);
        setUser(result.user);
        setIsNewUser(result.is_new);
        setInitData(telegramInitData);
        setIsTelegram(true);
        setIsDevMode(false);
        // Kick off /users/me/app-context immediately in parallel with the
        // ensuing render cycle so AppModeProvider can read it from cache
        // instead of triggering a fresh request.
        void prefetchAppContext(telegramInitData).catch(() => {});
        console.info("[PlanAm] Telegram auth success", {
          userId: result.user.id,
          isNew: result.is_new,
        });
      } catch (error) {
        const message = error instanceof Error ? error.message : "Auth failed";
        setAuthError(message);
        setUser(null);
        setIsNewUser(false);
        setInitData("");
      } finally {
        setIsAuthenticating(false);
      }
      return;
    }

    // Step 2: no Telegram initData. Try dev login if we look like a
    // local/preview environment.
    if (isClientDevMode()) {
      try {
        const result = await authenticateDevLogin();
        storeDevInitData(result.dev_init_data);
        setInitData(result.dev_init_data);
        setUser(result.user);
        setIsNewUser(result.is_new);
        setIsTelegram(false);
        setIsDevMode(true);
        setPlatform("dev");
        void prefetchAppContext(result.dev_init_data).catch(() => {});
        console.info("[PlanAm] Dev auth success", { userId: result.user.id });
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "Dev auth failed";
        setAuthError(message);
        setUser(null);
        setIsNewUser(false);
        setInitData("");
      } finally {
        setIsAuthenticating(false);
      }
      return;
    }

    // Step 3: genuinely outside Telegram and outside dev — show the
    // "open in Telegram" screen.
    debugAuthLog("No initData and no dev mode — falling back to TelegramRequired");
    setAuthError("Откройте приложение через Telegram");
    setUser(null);
    setInitData("");
    setIsTelegram(false);
    setIsDevMode(false);
    setIsAuthenticating(false);
  }, []);

  useEffect(() => {
    if (!mounted) {
      return;
    }
    void runAuth();
  }, [mounted, authAttempt, runAuth]);

  const value = useMemo<TelegramContextValue>(
    () => ({
      isTelegram,
      isDevMode,
      initData,
      platform,
      colorScheme,
      user,
      isNewUser,
      isAuthenticating,
      authError,
      retryAuth: () => setAuthAttempt((current) => current + 1),
    }),
    [
      authError,
      colorScheme,
      initData,
      isAuthenticating,
      isDevMode,
      isNewUser,
      isTelegram,
      platform,
      user,
    ],
  );

  if (!mounted) {
    return (
      <TelegramContext.Provider value={defaultContext}>
        {children}
      </TelegramContext.Provider>
    );
  }

  return (
    <TelegramContext.Provider value={value}>{children}</TelegramContext.Provider>
  );
}

export function useTelegram() {
  const context = useContext(TelegramContext);
  if (!context) {
    throw new Error("useTelegram must be used within TelegramProvider");
  }
  return context;
}
