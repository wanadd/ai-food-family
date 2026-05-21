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
import { fetchAppContext, updateAppMode } from "@/lib/app-mode/api";
import { loadStoredMode, saveStoredMode } from "@/lib/app-mode/storage";
import type { AppContext, AppMode } from "@/lib/app-mode/types";

type AppModeContextValue = {
  mode: AppMode;
  context: AppContext | null;
  loading: boolean;
  setMode: (mode: AppMode) => Promise<void>;
  refreshContext: () => Promise<void>;
};

const AppModeContext = createContext<AppModeContextValue | null>(null);

export function AppModeProvider({ children }: { children: ReactNode }) {
  const { initData, user } = useTelegram();
  const [mode, setModeState] = useState<AppMode>("personal");
  const [context, setContext] = useState<AppContext | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshContext = useCallback(async () => {
    if (!initData || !user) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const data = await fetchAppContext(initData);
      setContext(data);
      const stored = loadStoredMode();
      const nextMode =
        stored && stored === "family" && data.can_use_family_mode
          ? "family"
          : data.active_mode;
      setModeState(nextMode);
      saveStoredMode(nextMode);
    } catch {
      setContext(null);
      setModeState("personal");
    } finally {
      setLoading(false);
    }
  }, [initData, user]);

  useEffect(() => {
    refreshContext();
  }, [refreshContext]);

  const setMode = useCallback(
    async (nextMode: AppMode) => {
      if (!initData) {
        return;
      }
      const data = await updateAppMode(initData, nextMode);
      setContext(data);
      setModeState(data.active_mode);
      saveStoredMode(data.active_mode);
    },
    [initData],
  );

  const value = useMemo(
    () => ({
      mode,
      context,
      loading,
      setMode,
      refreshContext,
    }),
    [mode, context, loading, setMode, refreshContext],
  );

  return (
    <AppModeContext.Provider value={value}>{children}</AppModeContext.Provider>
  );
}

export function useAppMode() {
  const ctx = useContext(AppModeContext);
  if (!ctx) {
    throw new Error("useAppMode must be used within AppModeProvider");
  }
  return ctx;
}
