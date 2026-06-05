"use client";

import { usePathname } from "next/navigation";

import { useTelegramBackButton2026 } from "@/components/planam-2026/navigation/useTelegramBackButton2026";
import { shouldShowBack2026 } from "@/lib/navigation/back-navigation-2026";

type ScreenBack2026Props = {
  className?: string;
};

export function ScreenBack2026({ className }: ScreenBack2026Props) {
  const pathname = usePathname();
  const { goBack, useTelegramBack } = useTelegramBackButton2026(pathname);

  if (!shouldShowBack2026(pathname) || useTelegramBack) {
    return null;
  }

  return (
    <button
      type="button"
      onClick={goBack}
      className={
        className ??
        "shrink-0 rounded-control px-2 py-1 pa26-micro font-semibold text-sage-700 transition hover:bg-sage-50 dark:text-sage-300 dark:hover:bg-pa-elevated/50"
      }
      aria-label="Назад"
    >
      ← Назад
    </button>
  );
}
