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

import { authenticateWithTelegram, type AuthUser } from "@/lib/api";
import { getTelegramInitData, loadTelegramWebApp } from "@/lib/telegram-webapp";

type TelegramContextValue = {
  isTelegram: boolean;
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
  initData: "",
  platform: "unknown",
  colorScheme: "light",
  user: null,
  isNewUser: false,
  isAuthenticating: false,
  authError: null,
  retryAuth: () => {},
};

export function TelegramProvider({ children }: { children: ReactNode }) {
  const [mounted, setMounted] = useState(false);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isNewUser, setIsNewUser] = useState(false);
  const [isAuthenticating, setIsAuthenticating] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const [authAttempt, setAuthAttempt] = useState(0);
  const [initData, setInitData] = useState("");
  const [isTelegram, setIsTelegram] = useState(false);
  const [platform, setPlatform] = useState("unknown");
  const [colorScheme, setColorScheme] = useState("light");

  useEffect(() => {
    setMounted(true);

    async function init() {
      const webApp = await loadTelegramWebApp();
      if (!webApp) {
        return;
      }

      webApp.ready();
      webApp.expand();
      setInitData(webApp.initData);
      setIsTelegram(webApp.initData.length > 0);
      setPlatform(webApp.platform);
      setColorScheme(webApp.colorScheme);
      document.documentElement.style.setProperty(
        "--tg-theme-bg-color",
        webApp.themeParams.bg_color ?? "#f8fafc",
      );
    }

    init();
  }, []);

  const authenticate = useCallback(async () => {
    const telegramInitData = getTelegramInitData();
    if (!telegramInitData) {
      setAuthError("Откройте приложение через Telegram Mini App");
      return;
    }

    setIsAuthenticating(true);
    setAuthError(null);

    try {
      const result = await authenticateWithTelegram(telegramInitData);
      setUser(result.user);
      setIsNewUser(result.is_new);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Auth failed";
      setAuthError(message);
      setUser(null);
      setIsNewUser(false);
    } finally {
      setIsAuthenticating(false);
    }
  }, []);

  useEffect(() => {
    if (!mounted || !isTelegram) {
      return;
    }
    authenticate();
  }, [authenticate, authAttempt, isTelegram, mounted]);

  const value = useMemo<TelegramContextValue>(
    () => ({
      isTelegram,
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
