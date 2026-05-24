"use client";

import { useTelegram } from "@/components/TelegramProvider";

export type ProtectedScreenState =
  | "loading"
  | "ready"
  | "error"
  | "telegram_only";

/**
 * Unified auth gate for feature screens.
 * Never returns telegram_only when user is already authenticated.
 */
export function useProtectedScreen() {
  const ctx = useTelegram();
  const { user, initData, isAuthenticating, authError, isTelegram, isDevMode, retryAuth } =
    ctx;

  const isAuthenticated = Boolean(user);

  let state: ProtectedScreenState;
  if (isAuthenticating) {
    state = "loading";
  } else if (isAuthenticated && initData) {
    state = "ready";
  } else if (isAuthenticated && !initData) {
    state = "loading";
  } else if (authError) {
    state = "error";
  } else if (isTelegram || isDevMode) {
    state = "loading";
  } else {
    state = "telegram_only";
  }

  return {
    ...ctx,
    state,
    isAuthenticated,
    canFetch: Boolean(initData),
    retryAuth,
  };
}
