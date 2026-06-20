"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { NutritionistChat } from "@/components/nutritionist/NutritionistChat";
import { useSubscriptionOverview } from "@/components/subscription/SubscriptionProvider";
import { Skeleton2026 } from "@/components/planam-2026/ui/Skeleton2026";
import { useTelegram } from "@/components/TelegramProvider";
import { fetchSelectedMenu } from "@/lib/menu/api";
import type { MenuVariant } from "@/lib/menu/types";
import { fetchNutritionProfile } from "@/lib/nutrition-profile/api";
import type { NutritionProfileData } from "@/lib/nutrition-profile/types";
import { getNutritionistAskCost } from "@/lib/subscription/ama";

export function WellnessChat2026() {
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
    if (initData) {
      ensureSubscriptionLoaded();
    }
  }, [initData, ensureSubscriptionLoaded]);

  if (!initData) {
    return (
      <p className="px-4 py-16 text-center pa26-body text-pa-muted">
        Чат доступен в Telegram Mini App
      </p>
    );
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col px-4 pb-6 pt-2">
      <p className="pa26-caption text-pa-muted">
        Краткие ответы с учётом вашего профиля и меню
      </p>
      {loading ? (
        <Skeleton2026 variant="rect" className="mt-4 h-48 w-full" />
      ) : (
        <div className="mt-3 min-h-0 flex-1">
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
        </div>
      )}
      <p className="mt-4 text-center pa26-micro text-pa-muted">
        Рекомендации, не медицинские назначения.{" "}
        <Link
          href="/account/ams"
          className="font-semibold text-sage-700 dark:text-sage-300"
        >
          {amaBalance} Ам
        </Link>
      </p>
    </div>
  );
}
