"use client";

import { usePathname } from "next/navigation";

import { useTelegramBackButton2026 } from "@/components/planam-2026/navigation/useTelegramBackButton2026";

/** Wires Telegram WebApp BackButton on nested screens (no UI). */
export function TelegramBackBridge2026() {
  const pathname = usePathname();
  useTelegramBackButton2026(pathname);
  return null;
}
