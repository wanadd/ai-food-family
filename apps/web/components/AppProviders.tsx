"use client";

import type { ReactNode } from "react";

import { TelegramProvider } from "@/components/TelegramProvider";

export function AppProviders({ children }: { children: ReactNode }) {
  return <TelegramProvider>{children}</TelegramProvider>;
}
