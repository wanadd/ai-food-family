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
      href="/nutritionist/care"
      className="block rounded-2xl border border-violet-100 bg-gradient-to-br from-violet-50/80 to-white p-4 shadow-sm transition active:scale-[0.99]"
    >
      <p className="text-xs font-semibold uppercase tracking-wide text-violet-700">
        Telegram
      </p>
      <p className="mt-1 text-base font-bold text-stone-900">
        {active ? "Забота ПланАм активна" : "Настроить заботу в Telegram"}
      </p>
      <p className="mt-1 text-sm text-stone-600">Нажмите для настройки →</p>
    </Link>
  );
}
