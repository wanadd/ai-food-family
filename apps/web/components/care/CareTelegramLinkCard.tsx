"use client";

import Link from "next/link";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { useTelegram } from "@/components/TelegramProvider";
import { fetchCareSettings } from "@/lib/care/api";
import { useCallback, useEffect, useState } from "react";

export function CareTelegramLinkCard() {
  const { initData } = useTelegram();
  const { mode } = useAppMode();
  const [active, setActive] = useState(false);

  const load = useCallback(async () => {
    if (!initData) return;
    try {
      const settings = await fetchCareSettings(initData, mode);
      if (!settings) {
        setActive(false);
        return;
      }
      const anyOn =
        settings.menu_enabled ||
        settings.shopping_enabled ||
        settings.water_enabled ||
        settings.protein_enabled;
      setActive(anyOn);
    } catch {
      setActive(false);
    }
  }, [initData, mode]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <Link
      href="/notifications"
      className="pa-card block border-sage-200 bg-sage-50/40 p-4 transition active:scale-[0.99]"
    >
      <p className="text-xs font-semibold uppercase tracking-wide text-sage-700">
        Уведомления
      </p>
      <p className="mt-1 text-base font-bold text-graphite-900">
        {active
          ? "Забота ПланАм активна"
          : "Настроить заботливые напоминания"}
      </p>
      <p className="mt-1 text-sm text-graphite-600">
        Открыть настройки уведомлений →
      </p>
    </Link>
  );
}
