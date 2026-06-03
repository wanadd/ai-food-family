"use client";

import type { ReactNode } from "react";
import { useLayoutEffect } from "react";

import { AppModeProvider } from "@/components/app-mode/AppModeProvider";
import { AppGate } from "@/components/auth/AppGate";
import { captureAdminSessionFromUrl } from "@/lib/admin/session";
import { Onboarding2026Redirect } from "@/components/onboarding-2026/Onboarding2026Redirect";
import { AppShellBridge } from "@/components/layout/AppShellBridge";
import { SubscriptionProvider } from "@/components/subscription/SubscriptionProvider";
import { TelegramProvider } from "@/components/TelegramProvider";

function AdminSessionBootstrap() {
  useLayoutEffect(() => {
    captureAdminSessionFromUrl();
  }, []);
  return null;
}

export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <TelegramProvider>
      <AdminSessionBootstrap />
      <AppGate>
        <Onboarding2026Redirect>
          <AppModeProvider>
            <SubscriptionProvider>
              <AppShellBridge>{children}</AppShellBridge>
            </SubscriptionProvider>
          </AppModeProvider>
        </Onboarding2026Redirect>
      </AppGate>
    </TelegramProvider>
  );
}
