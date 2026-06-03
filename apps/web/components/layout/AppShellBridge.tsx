"use client";

import type { ReactNode } from "react";
import { usePathname } from "next/navigation";

import { AppShell2026 } from "@/components/planam-2026/layout/AppShell2026";
import { ThemeProvider } from "@/components/planam-2026/theme/ThemeProvider";
import { AppShell } from "@/components/layout/AppShell";
import { ToastProvider } from "@/components/ui/ToastProvider";
import { isPlanamUi2026Enabled } from "@/lib/planam/feature-flags";
import { isPlanamDevPreviewPath } from "@/lib/planam/theme";

export function AppShellBridge({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const isDevPreview = isPlanamDevPreviewPath(pathname);
  const isOnboarding = Boolean(pathname?.startsWith("/onboarding"));
  const use2026Shell = isPlanamUi2026Enabled() && !isDevPreview && !isOnboarding;

  if (isDevPreview || isOnboarding) {
    return (
      <ToastProvider>
        <ThemeProvider active>
          <div className="min-h-screen bg-pa-canvas text-pa-foreground">{children}</div>
        </ThemeProvider>
      </ToastProvider>
    );
  }

  if (use2026Shell) {
    return (
      <ToastProvider>
        <ThemeProvider active>
          <AppShell2026>{children}</AppShell2026>
        </ThemeProvider>
      </ToastProvider>
    );
  }

  return (
    <ToastProvider>
      <ThemeProvider active={false}>
        <AppShell>{children}</AppShell>
      </ThemeProvider>
    </ToastProvider>
  );
}
