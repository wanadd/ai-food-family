"use client";

import Link from "next/link";
import { useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { ScreenLayout } from "@/components/layout/ScreenLayout";
import { NutritionistChat } from "@/components/nutritionist/NutritionistChat";
import { useTelegram } from "@/components/TelegramProvider";
import { fetchNutritionProfile } from "@/lib/nutrition-profile/api";
import type { NutritionProfileData } from "@/lib/nutrition-profile/types";
import { fetchSelectedMenu } from "@/lib/menu/api";
import type { MenuVariant } from "@/lib/menu/types";
import { fetchSubscriptionOverview } from "@/lib/subscription/api";
import { getNutritionistAskCost } from "@/lib/subscription/ama";
import { useCallback, useEffect } from "react";

export default function NutritionistChatPage() {
  const { initData } = useTelegram();
  const { mode } = useAppMode();
  const [profile, setProfile] = useState<NutritionProfileData | null>(null);
  const [menu, setMenu] = useState<MenuVariant | null>(null);
  const [amaBalance, setAmaBalance] = useState(0);
  const [amaAskCost, setAmaAskCost] = useState(2);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!initData) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const [nutrition, selected, sub] = await Promise.all([
        fetchNutritionProfile(initData),
        fetchSelectedMenu(initData, mode).catch(() => null),
        fetchSubscriptionOverview(initData, mode),
      ]);
      setProfile(nutrition);
      setMenu(selected?.menu ?? null);
      if (sub) {
        setAmaBalance(sub.ama_balance);
        setAmaAskCost(getNutritionistAskCost(sub.ama_costs));
      }
    } finally {
      setLoading(false);
    }
  }, [initData, mode]);

  useEffect(() => {
    void load();
  }, [load]);

  if (!initData) {
    return (
      <div className="px-4 py-16 text-center text-sm text-stone-600">
        Чат доступен в Telegram Mini App
      </div>
    );
  }

  return (
    <ScreenLayout
      title="Чат нутрициолога"
      subtitle="Краткие ответы с учётом вашего профиля"
      back={{ label: "Нутрициолог", href: "/nutritionist" }}
      contentClassName="pb-4"
    >
      {loading ? (
        <p className="text-sm text-stone-500">Загрузка…</p>
      ) : (
        <NutritionistChat
          mode={mode}
          profile={profile}
          menu={menu}
          amaAskCost={amaAskCost}
          amaBalance={amaBalance}
          onBalanceChange={setAmaBalance}
        />
      )}
      <p className="mt-3 text-center text-xs text-stone-500">
        <Link href="/subscription" className="font-semibold text-emerald-700">
          Баланс Амов
        </Link>
        {" · "}
        {amaBalance} Ам
      </p>
    </ScreenLayout>
  );
}
