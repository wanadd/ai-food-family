"use client";

import type { ReactNode } from "react";

import { AppModeProvider } from "@/components/app-mode/AppModeProvider";
import { AppGate } from "@/components/auth/AppGate";
import { AppShell } from "@/components/layout/AppShell";
import { TelegramProvider } from "@/components/TelegramProvider";

export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <TelegramProvider>
      <AppGate>
        <AppModeProvider>
          <AppShell>{children}</AppShell>
        </AppModeProvider>
      </AppGate>
    </TelegramProvider>
  );
}
