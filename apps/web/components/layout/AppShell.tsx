"use client";

import type { ReactNode } from "react";

import { DevModeBanner } from "@/components/dev/DevModeBanner";
import { BottomNavigation } from "@/components/layout/BottomNavigation";
import { ToastProvider } from "@/components/ui/ToastProvider";
import { BOTTOM_NAV_OFFSET } from "@/lib/layout/constants";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <ToastProvider>
      <DevModeBanner />
      <div style={{ paddingBottom: BOTTOM_NAV_OFFSET }}>{children}</div>
      <BottomNavigation />
    </ToastProvider>
  );
}
