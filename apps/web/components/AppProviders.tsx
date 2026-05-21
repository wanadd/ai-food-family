"use client";

import type { ReactNode } from "react";

import { AppModeProvider } from "@/components/app-mode/AppModeProvider";
import { TelegramProvider } from "@/components/TelegramProvider";

export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <TelegramProvider>
      <AppModeProvider>{children}</AppModeProvider>
    </TelegramProvider>
  );
}
