"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect } from "react";

import {
  getBackFallback2026,
  shouldShowBack2026,
} from "@/lib/navigation/back-navigation-2026";
import { readTelegramWebApp } from "@/lib/telegram-webapp";

type TelegramBackButton = {
  isVisible: boolean;
  show: () => void;
  hide: () => void;
  onClick: (handler: () => void) => void;
  offClick: (handler: () => void) => void;
};

function getBackButton(): TelegramBackButton | null {
  const wa = readTelegramWebApp() as
    | (ReturnType<typeof readTelegramWebApp> & {
        BackButton?: TelegramBackButton;
      })
    | null;
  return wa?.BackButton ?? null;
}

export function useTelegramBackButton2026(pathname: string) {
  const router = useRouter();

  const goBack = useCallback(() => {
    if (typeof window !== "undefined" && window.history.length > 1) {
      router.back();
      return;
    }
    router.push(getBackFallback2026(pathname));
  }, [pathname, router]);

  useEffect(() => {
    const back = getBackButton();
    if (!back || !shouldShowBack2026(pathname)) {
      back?.hide();
      return;
    }

    back.show();
    back.onClick(goBack);
    return () => {
      back.offClick(goBack);
      back.hide();
    };
  }, [pathname, goBack]);

  return { goBack, useTelegramBack: Boolean(getBackButton()) };
}
