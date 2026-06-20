"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { ScreenLayout } from "@/components/layout/ScreenLayout";
import { useSubscriptionOverview } from "@/components/subscription/SubscriptionProvider";
import { useToast } from "@/components/ui/ToastProvider";
import { SkeletonCard, SkeletonList } from "@/components/ui/Skeleton";
import { useTelegram } from "@/components/TelegramProvider";
import { formatAmasBalance } from "@/lib/profile/billing";
import { selectPlanStub } from "@/lib/subscription/api";
import { AMA_ACTION_LABELS, formatAmaCost } from "@/lib/subscription/ama";
import type { SubscriptionOverview } from "@/lib/subscription/types";

function planPriceLabel(rub: number): string {
  if (rub <= 0) return "Бесплатно";
  return `${rub} ₽/мес`;
}

function planHighlights(plan: SubscriptionOverview["plans"][0]): string[] {
  const lines: string[] = [];
  lines.push(
    plan.max_profiles === 1
      ? "1 профиль"
      : `До ${plan.max_profiles} профилей`,
  );
  if (plan.monthly_menu_generations == null) {
    lines.push("Безлимитные генерации меню");
  } else {
    lines.push(`${plan.monthly_menu_generations} генераций меню`);
  }
  lines.push(`${plan.monthly_ams} Амов в месяц`);
  if (plan.features.nutritionist_extended) {
    lines.push("Расширенный нутрициолог");
  }
  if (plan.features.virtual_members) {
    lines.push("Виртуальные участники");
  }
  if (plan.features.macros) {
    lines.push("КБЖУ и аналитика");
  }
  return lines;
}

export function SubscriptionDashboard() {
  const { showToast } = useToast();
  const { initData, isTelegram } = useTelegram();
  const { mode } = useAppMode();
  const {
    overview: data,
    loading,
    ensureLoaded: ensureSubscriptionLoaded,
    patchOverview,
  } = useSubscriptionOverview();
  const [selecting, setSelecting] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    if (initData) ensureSubscriptionLoaded();
  }, [initData, ensureSubscriptionLoaded]);

  async function handleSelectPlan(planCode: string) {
    if (!initData) return;
    setSelecting(planCode);
    setMessage(null);
    try {
      const updated = await selectPlanStub(initData, mode, planCode);
      patchOverview(updated);
      await showToast("✓ Тариф сохранён");
    } catch (err) {
      setMessage(
        err instanceof Error
          ? err.message
          : "Не получилось сменить тариф. Попробуйте ещё раз через минуту.",
      );
    } finally {
      setSelecting(null);
    }
  }

  if (!initData && !isTelegram && !loading) {
    return (
      <div className="mx-auto max-w-lg px-4 py-16 text-center text-sm text-graphite-600">
        Тариф и баланс доступны в Telegram Mini App.
      </div>
    );
  }

  if (loading || !data) {
    return (
      <ScreenLayout title="Тариф" contentClassName="space-y-3 pb-24">
        <SkeletonCard titleWidth="w-1/3" lines={2} withButton />
        <SkeletonList count={2} />
      </ScreenLayout>
    );
  }

  const menuLimitLabel =
    data.menu_generations_limit == null
      ? "безлимит"
      : `${data.menu_generations_remaining ?? 0} из ${data.menu_generations_limit}`;

  return (
    <ScreenLayout
      title="Подписка"
      subtitle="Тариф и баланс Амов"
      back={{ label: "Профиль", href: "/profile" }}
      contentClassName="space-y-3"
    >
        {message ? (
          <p className="rounded-control border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            {message}
          </p>
        ) : null}

        <section className="pa-card border-sage-200 bg-sage-50/50 p-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-sage-700">
            Текущий тариф
          </p>
          <p className="mt-1 text-2xl font-bold text-graphite-900">{data.plan_name}</p>
          {data.status === "trial" && data.trial_days_left != null ? (
            <p className="mt-1 text-sm text-graphite-600">
              Пробный период · осталось {data.trial_days_left} дн.
            </p>
          ) : null}
          {!data.ai_actions_enabled ? (
            <p className="mt-2 text-sm font-medium text-warm">
              Сейчас AI-действия временно недоступны. Можно выбрать тариф —
              просмотр меню, покупок и запасов остаётся свободным.
            </p>
          ) : null}
        </section>

        <section className="grid grid-cols-2 gap-2">
          <article className="pa-card p-3">
            <p className="text-xs text-graphite-500">Генерации меню</p>
            <p className="mt-1 text-lg font-bold text-graphite-900">{menuLimitLabel}</p>
            <p className="mt-0.5 text-[11px] text-graphite-500">использовано {data.menu_generations_used}</p>
          </article>
          <article className="pa-card border-warm/30 bg-warm/10 p-3">
            <p className="text-xs text-graphite-700">
              {data.is_family_billing ? "Баланс семьи" : "Баланс Амов"}
            </p>
            <p className="mt-1 text-lg font-bold text-graphite-900">
              {formatAmasBalance(data.ama_balance)}
            </p>
            {data.is_family_billing && data.family_name ? (
              <p className="mt-0.5 text-[11px] text-graphite-500">
                {data.family_name}
              </p>
            ) : null}
          </article>
        </section>

        {data.is_family_billing && !data.can_spend_ama ? (
          <p className="rounded-control border border-cream-border bg-cream-deep px-4 py-3 text-sm text-graphite-600">
            Семейные Амы тратит администратор семьи. Участники без аккаунта
            учитываются в меню и советах.
          </p>
        ) : null}

        {(data.ama_transactions?.length ?? 0) > 0 ? (
          <section className="rounded-card border border-cream-border bg-cream-surface p-4 shadow-soft">
            <p className="text-sm font-bold text-graphite-900">История Амов</p>
            <ul className="mt-3 space-y-2">
              {data.ama_transactions?.map((tx) => (
                <li
                  key={tx.id}
                  className="flex items-start justify-between gap-2 border-b border-cream-border pb-2 text-sm last:border-0 last:pb-0"
                >
                  <div className="min-w-0">
                    <p className="font-medium text-graphite-900">{tx.user_name}</p>
                    <p className="text-xs text-graphite-500">{tx.reason_label}</p>
                  </div>
                  <span className="shrink-0 font-semibold text-red-700">
                    {tx.amount} Ам
                  </span>
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        <details className="rounded-card border border-cream-border bg-cream-surface p-4 shadow-soft">
          <summary className="cursor-pointer text-sm font-bold text-graphite-900">
            Что такое Амы
          </summary>
          <p className="mt-2 text-sm leading-relaxed text-graphite-600">
            Амы — внутренний ресурс ПланАм для дополнительных AI-действий: вопрос
            нутрициологу, разбор чека, голос, глубокий анализ. Просмотр меню,
            покупок и запасов Амы не тратит.
          </p>
          <ul className="mt-3 space-y-1 text-xs text-graphite-500">
            {Object.entries(data.ama_costs).slice(0, 5).map(([key, cost]) => (
              <li key={key} className="flex justify-between gap-2">
                <span>{AMA_ACTION_LABELS[key] ?? key}</span>
                <span className="font-medium text-graphite-700">
                  {formatAmaCost(cost)}
                </span>
              </li>
            ))}
          </ul>
        </details>

        <details className="rounded-card border border-cream-border bg-cream-surface p-4 shadow-soft">
          <summary className="cursor-pointer text-sm font-bold text-graphite-900">
            Подробнее о тарифах
          </summary>
          <ul className="mt-3 space-y-2">
            {data.plans.map((plan) => {
              const isCurrent = plan.is_current;
              return (
                <li
                  key={plan.code}
                  className={`rounded-card border p-4 ${
                    isCurrent
                      ? "border-sage-200 bg-sage-50/40"
                      : "border-cream-border bg-cream-surface"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="font-bold text-graphite-900">{plan.name}</p>
                      <p className="text-sm text-graphite-500">
                        {planPriceLabel(plan.price_rub)}
                      </p>
                    </div>
                    {isCurrent ? (
                      <span className="rounded-full bg-sage-600 px-2 py-0.5 text-xs font-semibold text-white">
                        Сейчас
                      </span>
                    ) : null}
                  </div>
                  <ul className="mt-2 space-y-0.5 text-sm text-graphite-600">
                    {planHighlights(plan).map((line) => (
                      <li key={line}>· {line}</li>
                    ))}
                  </ul>
                  {!isCurrent &&
                  (!data.is_family_billing || data.is_family_admin) ? (
                    <button
                      type="button"
                      disabled={Boolean(selecting)}
                      onClick={() => void handleSelectPlan(plan.code)}
                      className="mt-3 w-full rounded-control border border-cream-border py-2.5 text-sm font-semibold text-graphite-800 disabled:opacity-50"
                    >
                      {selecting === plan.code ? "…" : "Выбрать тариф"}
                    </button>
                  ) : null}
                </li>
              );
            })}
          </ul>
          <p className="mt-2 px-1 text-xs text-graphite-500">
            Оплата пока не подключена — выбор тарифа для теста без списания.
          </p>
        </details>

        <section className="pa-card border-dashed border-warm/30 bg-warm/5 p-4">
          <p className="font-semibold text-graphite-900">Пополнение баланса</p>
          <p className="mt-1 text-sm text-graphite-500">
            Покупка Амов появится в одном из следующих обновлений. До этого
            момента баланс пополняется ежемесячно по выбранному тарифу.
          </p>
          <button
            type="button"
            disabled
            className="mt-3 w-full rounded-control bg-cream-deep py-2.5 text-sm font-semibold text-graphite-400"
          >
            Скоро
          </button>
        </section>
    </ScreenLayout>
  );
}
