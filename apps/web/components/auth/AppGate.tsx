"use client";

import type { ReactNode } from "react";

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

  if (isTelegram && initData && !isAuthenticating && user && !user.phone_number) {
    return <PhoneRequiredScreen />;
  }

  return <>{children}</>;
}
