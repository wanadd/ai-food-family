"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { PaywallSheet2026 } from "@/components/monetization-2026/PaywallSheet2026";
import type { PaywallOpenOptions } from "@/lib/monetization/paywall";

type PaywallContextValue = {
  openPaywall: (options: PaywallOpenOptions) => void;
  closePaywall: () => void;
};

const PaywallContext = createContext<PaywallContextValue | null>(null);

export function PaywallProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<PaywallOpenOptions | null>(null);

  const openPaywall = useCallback((options: PaywallOpenOptions) => {
    setState(options);
  }, []);

  const closePaywall = useCallback(() => {
    setState(null);
  }, []);

  const value = useMemo(
    () => ({ openPaywall, closePaywall }),
    [openPaywall, closePaywall],
  );

  return (
    <PaywallContext.Provider value={value}>
      {children}
      <PaywallSheet2026
        open={state != null}
        options={state}
        onClose={closePaywall}
      />
    </PaywallContext.Provider>
  );
}

export function usePaywall2026(): PaywallContextValue {
  const ctx = useContext(PaywallContext);
  if (!ctx) {
    throw new Error("usePaywall2026 must be used within PaywallProvider");
  }
  return ctx;
}

/** Safe in legacy trees — returns null if provider missing. */
export function usePaywall2026Optional(): PaywallContextValue | null {
  return useContext(PaywallContext);
}
