"use client";

import type { ReactNode } from "react";
import { usePathname } from "next/navigation";

import { LegalConsentScreen } from "@/components/auth/LegalConsentScreen";
import { PhoneRequiredScreen } from "@/components/auth/PhoneRequiredScreen";
import { TelegramRequiredScreen } from "@/components/auth/TelegramRequiredScreen";
import { useTelegram } from "@/components/TelegramProvider";
import { isClientDevMode } from "@/lib/dev-auth";
import { isAuditModeEnabled, isAuditAuthReady } from "@/lib/audit/audit-mode";
import { captureAdminSessionFromUrl } from "@/lib/admin/session";
import { shouldBlockForPhone } from "@/lib/planam/onboarding-gate";

function isAdminRoute(pathname: string | null): boolean {
  return Boolean(pathname?.startsWith("/admin"));
}

function isPlanamDevPreviewRoute(pathname: string | null): boolean {
  return Boolean(pathname?.startsWith("/dev/planam-2026"));
}

function isOnboarding2026Route(pathname: string | null): boolean {
  return Boolean(pathname?.startsWith("/onboarding"));
}

function isPlanamAuditDevRoute(pathname: string | null): boolean {
  return Boolean(pathname?.startsWith("/dev/audit"));
}

function isExemptRoute(pathname: string | null): boolean {
  return (
    isAdminRoute(pathname) ||
    isPlanamDevPreviewRoute(pathname) ||
    isPlanamAuditDevRoute(pathname) ||
    isOnboarding2026Route(pathname)
  );
}

export function AppGate({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const {
    isTelegram,
    isDevMode,
    isAuditMode,
    user,
    isAuthenticating,
    initData,
    authError,
    auditAuthReady,
  } = useTelegram();

  if (typeof window !== "undefined") {
    captureAdminSessionFromUrl();
  }

  if (isExemptRoute(pathname)) {
    return <>{children}</>;
  }

  if (isAuthenticating) {
    return null;
  }

  if (isAuditModeEnabled() && !auditAuthReady && !authError) {
    return null;
  }

  if (
    isAuditModeEnabled() &&
    !isAuditAuthReady(initData, user, isAuthenticating) &&
    authError
  ) {
    return <TelegramRequiredScreen message={authError} />;
  }

  if (
    !isClientDevMode() &&
    !isDevMode &&
    !isAuditMode &&
    !isAuditModeEnabled() &&
    !user &&
    !isAuthenticating &&
    authError
  ) {
    return <TelegramRequiredScreen message={authError} />;
  }

  const needsLegal =
    user &&
    (!user.accepted_terms || !user.accepted_privacy || !user.accepted_personal_data);

  if (isTelegram && initData && !isAuthenticating && user && needsLegal) {
    return <LegalConsentScreen />;
  }

  const needsPhone =
    user &&
    shouldBlockForPhone(Boolean(user.phone_number), Boolean(user.phone_skipped)) &&
    user.accepted_terms &&
    user.accepted_privacy &&
    user.accepted_personal_data;

  if (isTelegram && initData && !isAuthenticating && needsPhone) {
    return <PhoneRequiredScreen />;
  }

  return <>{children}</>;
}
