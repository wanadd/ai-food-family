"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { useTelegram } from "@/components/TelegramProvider";
import { fetchSubscriptionOverview } from "@/lib/subscription/api";
import type { SubscriptionOverview } from "@/lib/subscription/types";

type SubscriptionContextValue = {
  overview: SubscriptionOverview | null;
  loading: boolean;
  error: string | null;
  /**
   * Triggers a fetch if cache is empty for the current (initData, mode) key.
   * Idempotent — safe to call from many components.
   */
  ensureLoaded: () => void;
  /**
   * Forces a fresh fetch (invalidates cache). Call after operations that
   * change Ama balance (quick actions, dish replace, AI calls, plan switch).
   */
  refresh: () => Promise<SubscriptionOverview | null>;
  /**
   * Applies a partial patch to the cached overview without hitting the
   * network. Useful for optimistic updates (e.g. chat reply decremented
   * balance by askCost — preserve UX without extra fetch).
   */
  patchOverview: (patch: Partial<SubscriptionOverview>) => void;
};

const SubscriptionContext = createContext<SubscriptionContextValue | null>(
  null,
);

export function SubscriptionProvider({ children }: { children: ReactNode }) {
  const { initData } = useTelegram();
  const { mode } = useAppMode();

  const [overview, setOverview] = useState<SubscriptionOverview | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const inFlightRef = useRef<Promise<SubscriptionOverview | null> | null>(null);
  const lastKeyRef = useRef<string | null>(null);
  const currentKey = initData ? `${mode}::${initData.slice(0, 16)}` : null;

  // Invalidate cache when auth/mode key changes.
  useEffect(() => {
    if (lastKeyRef.current !== currentKey) {
      lastKeyRef.current = currentKey;
      setOverview(null);
      setError(null);
      inFlightRef.current = null;
    }
  }, [currentKey]);

  const doFetch = useCallback(async (): Promise<SubscriptionOverview | null> => {
    if (!initData) return null;
    if (inFlightRef.current) return inFlightRef.current;
    setLoading(true);
    setError(null);
    const request = (async () => {
      try {
        const data = await fetchSubscriptionOverview(initData, mode);
        setOverview(data);
        return data;
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Не удалось загрузить тариф";
        setError(message);
        return null;
      } finally {
        setLoading(false);
        inFlightRef.current = null;
      }
    })();
    inFlightRef.current = request;
    return request;
  }, [initData, mode]);

  const ensureLoaded = useCallback(() => {
    if (!initData) return;
    if (overview || inFlightRef.current) return;
    void doFetch();
  }, [doFetch, initData, overview]);

  const refresh = useCallback(async () => {
    if (!initData) return null;
    inFlightRef.current = null;
    return doFetch();
  }, [doFetch, initData]);

  const patchOverview = useCallback(
    (patch: Partial<SubscriptionOverview>) => {
      setOverview((current) => (current ? { ...current, ...patch } : current));
    },
    [],
  );

  const value = useMemo<SubscriptionContextValue>(
    () => ({
      overview,
      loading,
      error,
      ensureLoaded,
      refresh,
      patchOverview,
    }),
    [overview, loading, error, ensureLoaded, refresh, patchOverview],
  );

  return (
    <SubscriptionContext.Provider value={value}>
      {children}
    </SubscriptionContext.Provider>
  );
}

export function useSubscriptionOverview(): SubscriptionContextValue {
  const ctx = useContext(SubscriptionContext);
  if (!ctx) {
    throw new Error(
      "useSubscriptionOverview must be used within SubscriptionProvider",
    );
  }
  return ctx;
}
