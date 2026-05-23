"use client";

import type { ReactNode } from "react";

import { LegalConsentScreen } from "@/components/auth/LegalConsentScreen";
import { PhoneRequiredScreen } from "@/components/auth/PhoneRequiredScreen";
import { TelegramRequiredScreen } from "@/components/auth/TelegramRequiredScreen";
import { useTelegram } from "@/components/TelegramProvider";
import { isClientDevMode } from "@/lib/dev-auth";

export function AppGate({ children }: { children: ReactNode }) {
  const { isTelegram, isDevMode, user, isAuthenticating, initData, authError } =
    useTelegram();

  if (
    !isClientDevMode() &&
    !isDevMode &&
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
    !user.phone_number &&
    !user.phone_skipped &&
    user.accepted_terms &&
    user.accepted_privacy &&
    user.accepted_personal_data;

  if (isTelegram && initData && !isAuthenticating && needsPhone) {
    return <PhoneRequiredScreen />;
  }

  return <>{children}</>;
}
