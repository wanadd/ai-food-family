"use client";

import type { ReactNode } from "react";

import { PhoneRequiredScreen } from "@/components/auth/PhoneRequiredScreen";
import { useTelegram } from "@/components/TelegramProvider";

export function AppGate({ children }: { children: ReactNode }) {
  const { isTelegram, user, isAuthenticating, initData } = useTelegram();

  if (isTelegram && initData && !isAuthenticating && user && !user.phone_number) {
    return <PhoneRequiredScreen />;
  }

  return <>{children}</>;
}
