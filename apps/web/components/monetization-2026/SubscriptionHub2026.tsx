"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { PlanCard2026 } from "@/components/monetization-2026/PlanCard2026";
import { TrialStatus2026 } from "@/components/monetization-2026/TrialStatus2026";
import { Button2026 } from "@/components/planam-2026/ui/Button2026";
import { Card2026 } from "@/components/planam-2026/ui/Card2026";
import { EmptyState2026 } from "@/components/planam-2026/ui/EmptyState2026";
import { Skeleton2026 } from "@/components/planam-2026/ui/Skeleton2026";
import { useSubscriptionOverview } from "@/components/subscription/SubscriptionProvider";
import { useTelegram } from "@/components/TelegramProvider";
import {
  formatPeriodEnd,
  isOnTrial,
} from "@/lib/monetization/billing-status";
import {
  catalogEntryForCode,
  filterRetailPlans,
  isRetailPlanCode,
  planDisplayName,
  sortRetailPlans,
} from "@/lib/monetization/plan-catalog-2026";
import {
  MONETIZATION_PATHS,
  subscriptionCheckoutPath,
} from "@/lib/monetization/paths";
import { PLAN_CATALOG_2026 } from "@/lib/monetization/plan-catalog-2026";
import { formatAmasBalance } from "@/lib/profile/billing";

export function SubscriptionHub2026() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const highlight = searchParams.get("highlight");
  const { initData, isTelegram } = useTelegram();
  const { mode } = useAppMode();
  const { overview: data, loading, ensureLoaded } = useSubscriptionOverview();
  const [selecting, setSelecting] = useState<string | null>(null);

  useEffect(() => {
    if (initData) {
      ensureLoaded();
    }
  }, [initData, ensureLoaded]);

  const retailPlans = useMemo(() => {
    if (!data?.plans) {
      return [];
    }
    return sortRetailPlans(filterRetailPlans(data.plans));
  }, [data?.plans]);

  function handleUpgrade(planCode: string) {
    router.push(subscriptionCheckoutPath(planCode));
  }

  if (!initData && !isTelegram && !loading) {
    return (
      <p className="px-4 py-16 text-center pa26-body text-pa-muted">
        Подписка доступна в Telegram Mini App
      </p>
    );
  }

  if (loading || !data) {
    return (
      <div className="space-y-3 px-4 py-6">
        <Skeleton2026 variant="rect" className="h-28 w-full" />
        <Skeleton2026 variant="rect" className="h-40 w-full" />
        <Skeleton2026 variant="rect" className="h-48 w-full" />
      </div>
    );
  }

  const menuLimitLabel =
    data.menu_generations_limit == null
      ? "безлимит"
      : `${data.menu_generations_remaining ?? 0} из ${data.menu_generations_limit}`;

  const periodEnd = formatPeriodEnd(data.current_period_ends_at);
  const trial = isOnTrial(data);

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
              {data.is_family_billing ? "Амы семьи" : "Амы"}
            </p>
            <p className="pa26-card-title mt-1 tabular-nums">
              {formatAmasBalance(data.ama_balance)}
            </p>
            <p className="pa26-micro mt-1 font-semibold text-sage-700 dark:text-sage-300">
              История →
            </p>
          </Card2026>
        </Link>
      </div>

      <section>
        <h2 className="pa26-section-title px-1">Тарифы</h2>
        <p className="pa26-caption mb-3 px-1 text-pa-muted">
          Старт · Пара · Семья · PRO — без скрытых комиссий
        </p>
        <div className="space-y-3">
          {retailPlans.map((apiPlan) => {
            const catalog = catalogEntryForCode(apiPlan.code);
            if (!catalog) {
              return null;
            }
            const isHighlight =
              highlight === apiPlan.code ||
              (highlight === "pro" && catalog.isPro);
            return (
              <div
                key={apiPlan.code}
                id={isHighlight ? "plan-highlight" : undefined}
                className={
                  isHighlight ? "scroll-mt-4 rounded-card ring-2 ring-sage-400/60" : undefined
                }
              >
                <PlanCard2026
                  catalog={catalog}
                  apiPlan={apiPlan}
                  isCurrent={apiPlan.is_current}
                  selecting={selecting === apiPlan.code}
                  onSelect={(code) => {
                    setSelecting(code);
                    handleUpgrade(code);
                    setSelecting(null);
                  }}
                />
              </div>
            );
          })}
        </div>
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
        {data.plan_code !== "pro" ? (
          <Button2026
            size="wide"
            className="mt-4"
            onClick={() => handleUpgrade("pro")}
          >
            Перейти на PRO
          </Button2026>
        ) : null}
      </Card2026>

      <p className="px-1 text-center pa26-micro text-pa-muted">
        Оплата картой и Telegram Stars — в следующем обновлении. Сейчас выбор
        тарифа сохраняется для теста.
      </p>
    </div>
  );
}
