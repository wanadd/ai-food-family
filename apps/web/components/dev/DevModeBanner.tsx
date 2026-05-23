"use client";

import { useTelegram } from "@/components/TelegramProvider";
import { isClientDevMode } from "@/lib/dev-auth";

export function DevModeBanner() {
  const { isDevMode, user } = useTelegram();

  if (!isClientDevMode() || !isDevMode) {
    return null;
  }

  const label =
    user?.first_name && user.username
      ? `${user.first_name} (@${user.username})`
      : "тестовый пользователь";

  return (
    <div
      className="border-b border-amber-300 bg-amber-100 px-3 py-2 text-center text-xs font-medium text-amber-950"
      role="status"
    >
      DEV режим: {label}
    </div>
  );
}
