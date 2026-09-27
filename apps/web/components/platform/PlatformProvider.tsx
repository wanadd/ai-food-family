"use client";

import { createContext, useContext, useEffect, useMemo, type ReactNode } from "react";

import { installViewportListener, type PlatformAdapter } from "@/lib/platform/adapter";
import { createTelegramPlatformAdapter } from "@/lib/platform/telegram-adapter";
import { webPlatformAdapter } from "@/lib/platform/web-adapter";

const PlatformContext = createContext<PlatformAdapter>(webPlatformAdapter);

export function PlatformProvider({ children }: { children: ReactNode }) {
  const adapter = useMemo(() => createTelegramPlatformAdapter() ?? webPlatformAdapter, []);

  useEffect(() => {
    const removeViewportListener = installViewportListener();
    document.documentElement.dataset.planamClient = adapter.clientType;
    if (adapter.clientType === "telegram") {
      void adapter.requestFullscreen();
    }
    return removeViewportListener;
  }, [adapter]);

  return <PlatformContext.Provider value={adapter}>{children}</PlatformContext.Provider>;
}

export function usePlatform(): PlatformAdapter {
  return useContext(PlatformContext);
}
