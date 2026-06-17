"use client";

import { useEffect, type ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";

import { useTelegram } from "@/components/TelegramProvider";
import { isPlanamUi2026Enabled } from "@/lib/planam/feature-flags";
import { isWowComplete, markWowComplete } from "@/lib/planam/onboarding-gate";
import {
  auditPersonaSkipsOnboarding,
  getStoredAuditPersona,
  isAuditModeEnabled,
} from "@/lib/audit/audit-mode";

const BYPASS_PREFIXES = ["/onboarding", "/admin", "/dev"];

function isBypassPath(pathname: string | null): boolean {
  if (!pathname) return false;
  return BYPASS_PREFIXES.some((p) => pathname.startsWith(p));
}

/**
 * Новые пользователи (UI 2026) → /onboarding до markWowComplete().
 */
export function Onboarding2026Redirect({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isNewUser, isAuthenticating } = useTelegram();

  useEffect(() => {
    if (!isPlanamUi2026Enabled()) return;
    if (isBypassPath(pathname)) return;
    if (isAuthenticating || !user) return;
    if (isAuditModeEnabled()) {
      const persona = getStoredAuditPersona();
      if (auditPersonaSkipsOnboarding(persona)) {
        if (!isWowComplete()) markWowComplete();
        return;
      }
    }
    if (isWowComplete()) return;
    if (isNewUser) {
      router.replace("/onboarding");
    }
  }, [pathname, router, user, isNewUser, isAuthenticating]);

  return <>{children}</>;
}
