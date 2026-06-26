"use client";

import Link from "next/link";
import { useEffect } from "react";

import { SubscriptionOffline2026 } from "@/components/monetization-2026/SubscriptionOffline2026";
import { TrialStatus2026 } from "@/components/monetization-2026/TrialStatus2026";
import { Card2026 } from "@/components/planam-2026/ui/Card2026";
import { Skeleton2026 } from "@/components/planam-2026/ui/Skeleton2026";
import { useSubscriptionOverview } from "@/components/subscription/SubscriptionProvider";
import { useTelegram } from "@/components/TelegramProvider";
import {
  formatPeriodEnd,
  isOnTrial,
} from "@/lib/monetization/billing-status";
import { planDisplayName } from "@/lib/monetization/plan-catalog-2026";
import { MONETIZATION_PATHS } from "@/lib/monetization/paths";
import { PLAN_CATALOG_2026 } from "@/lib/monetization/plan-catalog-2026";
import { formatAmasBalance } from "@/lib/profile/billing";

export function SubscriptionHub2026() {
  const { initData } = useTelegram();
  const {
    overview: data,
    loading,
    error,
    ensureLoaded,
    refresh,
  } = useSubscriptionOverview();

  useEffect(() => {
    if (initData) {
      ensureLoaded();
    }
  }, [initData, ensureLoaded]);

  if (!initData) {
    return <SubscriptionOffline2026 />;
  }

  if ((loading && !data) || (error && !data)) {
    if (error && !loading) {
      return (
        <SubscriptionOffline2026 onRetry={() => void refresh()} />
      );
    }
    return (
      <div className="space-y-3 px-4 py-6">
        <Skeleton2026 variant="rect" className="h-28 w-full" />
        <Skeleton2026 variant="rect" className="h-40 w-full" />
        <Skeleton2026 variant="rect" className="h-48 w-full" />
      </div>
    );
  }

  if (!data) {
    return <SubscriptionOffline2026 onRetry={() => void refresh()} />;
  }

  const trial = isOnTrial(data);
  const periodEnd = formatPeriodEnd(data.current_period_ends_at);

  const menuLimitLabel =
    data.menu_generations_limit == null
      ? "безлимит"
      : trial
        ? `Осталось ${data.menu_generations_remaining ?? 0} подборов меню`
        : `Осталось ${data.menu_generations_remaining ?? 0} подборов меню`;

  return (
    <div className="space-y-4 px-4 pb-8 pt-2">
      {trial ? <TrialStatus2026 overview={data} /> : null}

      <Card2026>
        <p className="pa26-micro font-semibold uppercase tracking-wide text-sage-700 dark:text-sage-300">
          Текущий тариф
        </p>
        <p className="pa26-page-title mt-1">
          {planDisplayName(data.plan_code, data.plan_name)}
        </p>
        {periodEnd && !trial ? (
          <p className="pa26-caption mt-1 text-pa-muted">
            Действует до {periodEnd}
          </p>
        ) : null}
        {!data.ai_actions_enabled ? (
          <p className="pa26-caption mt-2 text-warm">
            AI-действия временно недоступны — меню и покупки работают.
          </p>
        ) : null}
      </Card2026>

      <div className="grid grid-cols-2 gap-2">
        <Card2026 className="p-3">
          <p className="pa26-micro text-pa-muted">Генерации</p>
          <p className="pa26-card-title mt-1 tabular-nums">{menuLimitLabel}</p>
        </Card2026>
        <Link href={MONETIZATION_PATHS.ams} className="block">
          <Card2026 className="h-full border-sage-200 bg-sage-50/50 p-3 dark:border-sage-700/40 dark:bg-sage-700/15">
            <p className="pa26-micro text-pa-muted">
              {data.is_family_billing ? "Амы — AI-действия семьи" : "Амы — AI-действия"}
            </p>
            <p className="pa26-card-title mt-1 tabular-nums">
              {formatAmasBalance(data.ama_balance)}
            </p>
            <p className="pa26-micro mt-1 text-pa-muted">
              Например: 1 разбор рациона или AI-совет
            </p>
            <p className="pa26-micro mt-1 font-semibold text-sage-700 dark:text-sage-300">
              История →
            </p>
          </Card2026>
        </Link>
      </div>

      <section>
        <h2 className="pa26-section-title px-1">Тариф</h2>
        <Card2026 padding="md">
          <p className="pa26-body text-pa-muted">
            Смена тарифа доступна только через администратора. Напишите в поддержку,
            если нужно изменить план или продлить доступ.
          </p>
          {trial && periodEnd ? (
            <p className="pa26-caption mt-2 text-pa-muted">
              Стартовый доступ до {periodEnd}
            </p>
          ) : null}
        </Card2026>
      </section>

      <Card2026 className="border-dashed">
        <p className="pa26-card-title">Преимущества PRO</p>
        <ul className="mt-2 space-y-1">
          {PLAN_CATALOG_2026.pro.benefits.map((b) => (
            <li key={b} className="pa26-caption text-pa-muted">
              · {b}
            </li>
          ))}
        </ul>
      </Card2026>
    </div>
  );
}
