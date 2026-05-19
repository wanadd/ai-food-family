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
import WebApp from "@twa-dev/sdk";

import { authenticateWithTelegram, type AuthUser } from "@/lib/api";

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

export function TelegramProvider({ children }: { children: ReactNode }) {
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
    WebApp.ready();
    WebApp.expand();
    setInitData(WebApp.initData);
    setIsTelegram(WebApp.initData.length > 0);
    setPlatform(WebApp.platform);
    setColorScheme(WebApp.colorScheme);
    document.documentElement.style.setProperty(
      "--tg-theme-bg-color",
      WebApp.themeParams.bg_color ?? "#f8fafc",
    );
  }, []);

  const authenticate = useCallback(async () => {
    if (!WebApp.initData) {
      setAuthError("Откройте приложение через Telegram Mini App");
      return;
    }

    setIsAuthenticating(true);
    setAuthError(null);

    try {
      const result = await authenticateWithTelegram(WebApp.initData);
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
    if (!isTelegram) {
      return;
    }
    authenticate();
  }, [authenticate, authAttempt, isTelegram]);

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
