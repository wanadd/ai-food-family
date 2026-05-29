"use client";

import Link from "next/link";
import { useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { ScreenLayout } from "@/components/layout/ScreenLayout";
import { NutritionistChat } from "@/components/nutritionist/NutritionistChat";
import { useSubscriptionOverview } from "@/components/subscription/SubscriptionProvider";
import { useTelegram } from "@/components/TelegramProvider";
import { fetchNutritionProfile } from "@/lib/nutrition-profile/api";
import type { NutritionProfileData } from "@/lib/nutrition-profile/types";
import { fetchSelectedMenu } from "@/lib/menu/api";
import type { MenuVariant } from "@/lib/menu/types";
import { getNutritionistAskCost } from "@/lib/subscription/ama";
import { useCallback, useEffect } from "react";

export default function HealthChatPage() {
  const { initData } = useTelegram();
  const { mode } = useAppMode();
  const {
    overview: subscription,
    ensureLoaded: ensureSubscriptionLoaded,
    patchOverview: patchSubscription,
  } = useSubscriptionOverview();
  const [profile, setProfile] = useState<NutritionProfileData | null>(null);
  const [menu, setMenu] = useState<MenuVariant | null>(null);
  const [loading, setLoading] = useState(true);

  const amaBalance = subscription?.ama_balance ?? 0;
  const amaAskCost = getNutritionistAskCost(subscription?.ama_costs);

  const load = useCallback(async () => {
    if (!initData) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const [nutrition, selected] = await Promise.all([
        fetchNutritionProfile(initData),
        fetchSelectedMenu(initData, mode).catch(() => null),
      ]);
      setProfile(nutrition);
      setMenu(selected?.menu ?? null);
    } finally {
      setLoading(false);
    }
  }, [initData, mode]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (initData) ensureSubscriptionLoaded();
  }, [initData, ensureSubscriptionLoaded]);

  if (!initData) {
    return (
      <div className="px-4 py-16 text-center text-sm text-graphite-600">
        Чат доступен в Telegram Mini App
      </div>
    );
  }

  return (
    <ScreenLayout
      title="Чат нутрициолога"
      subtitle="Краткие ответы с учётом вашего профиля"
      back={{ label: "Здоровье", href: "/health" }}
      contentClassName="pb-4"
    >
      {loading ? (
        <p className="text-sm text-graphite-500">Загрузка…</p>
      ) : (
        <NutritionistChat
          mode={mode}
          profile={profile}
          menu={menu}
          amaAskCost={amaAskCost}
          amaBalance={amaBalance}
          onBalanceChange={(balance) =>
            patchSubscription({ ama_balance: balance })
          }
        />
      )}
      <p className="mt-3 text-center text-xs text-graphite-500">
        <Link href="/subscription" className="font-semibold text-sage-700">
          Баланс Амов
        </Link>
        {" · "}
        {amaBalance} Ам
      </p>
    </ScreenLayout>
  );
}
