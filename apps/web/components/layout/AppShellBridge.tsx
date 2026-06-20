"use client";

import type { ReactNode } from "react";
import { usePathname } from "next/navigation";

import { AppShell2026 } from "@/components/planam-2026/layout/AppShell2026";
import { ThemeProvider } from "@/components/planam-2026/theme/ThemeProvider";
import { AppShell } from "@/components/layout/AppShell";
import { ToastProvider } from "@/components/ui/ToastProvider";
import { isPlanamUi2026Enabled } from "@/lib/planam/feature-flags";
import { isPlanamDevPreviewPath } from "@/lib/planam/theme";

function isAuditDevPath(pathname: string | null): boolean {
  return Boolean(pathname?.startsWith("/dev/audit"));
}

export function AppShellBridge({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const isDevPreview = isPlanamDevPreviewPath(pathname);
  const isAuditDev = isAuditDevPath(pathname);
  const isOnboarding = Boolean(pathname?.startsWith("/onboarding"));
  const use2026Shell =
    isPlanamUi2026Enabled() && !isDevPreview && !isAuditDev && !isOnboarding;

  if (isDevPreview || isAuditDev || isOnboarding) {
    return (
      <ToastProvider>
        <ThemeProvider active scope2026>
          <div className="min-h-screen bg-pa-canvas text-pa-foreground">{children}</div>
        </ThemeProvider>
      </ToastProvider>
    );
  }

  if (use2026Shell) {
    return (
      <ToastProvider>
        <ThemeProvider active scope2026>
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
