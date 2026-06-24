"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect } from "react";

import {
  resolveBackTarget2026,
  shouldShowBack2026,
} from "@/lib/navigation/back-navigation-2026";
import { RETURN_TO_PARAM } from "@/lib/navigation/return-to";
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

export function useTelegramBackButton2026(
  pathname: string,
  options: { wireTelegram?: boolean } = {},
) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const hasReturnTo = Boolean(searchParams.get(RETURN_TO_PARAM));
  const wireTelegram = options.wireTelegram ?? true;

  const goBack = useCallback(() => {
    const target = resolveBackTarget2026(pathname, searchParams);
    if (hasReturnTo) {
      router.push(target);
      return;
    }
    if (typeof window !== "undefined" && window.history.length > 1) {
      router.back();
      return;
    }
    router.push(target);
  }, [pathname, searchParams, hasReturnTo, router]);

  useEffect(() => {
    if (!wireTelegram) {
      return;
    }
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
  }, [pathname, goBack, wireTelegram]);

  return { goBack, useTelegramBack: wireTelegram && Boolean(getBackButton()) };
}
