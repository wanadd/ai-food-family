"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

type ToastState = {
  message: string;
  visible: boolean;
};

type ToastContextValue = {
  showToast: (message: string, durationMs?: number) => Promise<void>;
};

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toast, setToast] = useState<ToastState>({ message: "", visible: false });

  const showToast = useCallback((message: string, durationMs = 1800) => {
    return new Promise<void>((resolve) => {
      setToast({ message, visible: true });
      window.setTimeout(() => {
        setToast({ message: "", visible: false });
        resolve();
      }, durationMs);
    });
  }, []);

  const value = useMemo(() => ({ showToast }), [showToast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      {toast.visible ? (
        <div
          className="pointer-events-none fixed left-1/2 top-[max(1rem,env(safe-area-inset-top))] z-[60] -translate-x-1/2"
          role="status"
          aria-live="polite"
        >
          <p className="rounded-2xl bg-stone-900/95 px-5 py-3 text-sm font-semibold text-white shadow-lg">
            {toast.message}
          </p>
        </div>
      ) : null}
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return ctx;
}
