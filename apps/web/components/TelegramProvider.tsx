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
import { isClientDevMode, storeDevInitData } from "@/lib/dev-auth";
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

function readTelegramInitData(): string {
  if (typeof window === "undefined") {
    return "";
  }
  return (
    (window as Window & { Telegram?: { WebApp?: { initData?: string } } }).Telegram
      ?.WebApp?.initData ?? ""
  );
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

    void (async () => {
      const webApp = await loadTelegramWebApp();
      if (webApp?.initData) {
        webApp.ready();
        webApp.expand();
        setPlatform(webApp.platform);
        setColorScheme(webApp.colorScheme);
        document.documentElement.style.setProperty(
          "--tg-theme-bg-color",
          webApp.themeParams.bg_color ?? "#f8fafc",
        );
      } else if (isClientDevMode()) {
        setPlatform("dev");
      }
    })();
  }, []);

  const runAuth = useCallback(async () => {
    const telegramInitData = readTelegramInitData();

    if (telegramInitData.length > 0) {
      setIsAuthenticating(true);
      setAuthError(null);
      try {
        const result = await authenticateWithTelegram(telegramInitData);
        setUser(result.user);
        setIsNewUser(result.is_new);
        setInitData(telegramInitData);
        setIsTelegram(true);
        setIsDevMode(false);
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

    if (isClientDevMode()) {
      setIsAuthenticating(true);
      setAuthError(null);
      try {
        const result = await authenticateDevLogin();
        storeDevInitData(result.dev_init_data);
        setInitData(result.dev_init_data);
        setUser(result.user);
        setIsNewUser(result.is_new);
        setIsTelegram(false);
        setIsDevMode(true);
        setPlatform("dev");
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

    setAuthError("Откройте приложение через Telegram");
    setUser(null);
    setInitData("");
    setIsTelegram(false);
    setIsDevMode(false);
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
