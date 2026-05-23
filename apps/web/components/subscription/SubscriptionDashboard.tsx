"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { ScreenLayout } from "@/components/layout/ScreenLayout";
import { useToast } from "@/components/ui/ToastProvider";
import { PageLoading } from "@/components/ui/PageLoading";
import { useTelegram } from "@/components/TelegramProvider";
import { formatAmasBalance } from "@/lib/profile/billing";
import {
  fetchSubscriptionOverview,
  selectPlanStub,
} from "@/lib/subscription/api";
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
  const router = useRouter();
  const { showToast } = useToast();
  const { initData, isTelegram } = useTelegram();
  const { mode } = useAppMode();
  const [data, setData] = useState<SubscriptionOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [selecting, setSelecting] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!initData) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const overview = await fetchSubscriptionOverview(initData, mode);
      setData(overview);
    } finally {
      setLoading(false);
    }
  }, [initData, mode]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleSelectPlan(planCode: string) {
    if (!initData) return;
    setSelecting(planCode);
    setMessage(null);
    try {
      const updated = await selectPlanStub(initData, mode, planCode);
      setData(updated);
      await showToast("✓ Сохранено");
      router.push("/profile");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Не удалось сменить тариф");
    } finally {
      setSelecting(null);
    }
  }

  if (!initData && !isTelegram && !loading) {
    return (
      <div className="mx-auto max-w-lg px-4 py-16 text-center text-sm text-stone-600">
        Откройте приложение в Telegram
      </div>
    );
  }

  if (loading || !data) {
    return (
      <div className="min-h-screen bg-stone-50">
        <PageLoading message="Загрузка тарифа…" />
      </div>
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
          <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            {message}
          </p>
        ) : null}

        <section className="rounded-2xl border border-emerald-100 bg-gradient-to-br from-emerald-50 to-white p-4 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800">
            Текущий тариф
          </p>
          <p className="mt-1 text-2xl font-bold text-stone-900">{data.plan_name}</p>
          {data.status === "trial" && data.trial_days_left != null ? (
            <p className="mt-1 text-sm text-stone-600">
              Пробный период · осталось {data.trial_days_left} дн.
            </p>
          ) : null}
          {!data.ai_actions_enabled ? (
            <p className="mt-2 text-sm font-medium text-amber-800">
              Новые AI-действия недоступны — выберите тариф
            </p>
          ) : null}
        </section>

        <section className="grid grid-cols-2 gap-2">
          <article className="rounded-2xl border border-stone-100 bg-white p-3 shadow-sm">
            <p className="text-xs text-stone-500">Генерации меню</p>
            <p className="mt-1 text-lg font-bold text-stone-900">{menuLimitLabel}</p>
            <p className="mt-0.5 text-[11px] text-stone-500">использовано {data.menu_generations_used}</p>
          </article>
          <article className="rounded-2xl border border-amber-100 bg-amber-50/50 p-3 shadow-sm">
            <p className="text-xs text-amber-800">
              {data.is_family_billing ? "Баланс семьи" : "Баланс Амов"}
            </p>
            <p className="mt-1 text-lg font-bold text-amber-950">
              {formatAmasBalance(data.ama_balance)}
            </p>
            {data.is_family_billing && data.family_name ? (
              <p className="mt-0.5 text-[11px] text-amber-900/80">
                {data.family_name}
              </p>
            ) : null}
          </article>
        </section>

        {data.is_family_billing && !data.can_spend_ama ? (
          <p className="rounded-xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm text-stone-600">
            Семейные Амы тратит администратор семьи. Участники без аккаунта
            учитываются в меню и советах.
          </p>
        ) : null}

        {(data.ama_transactions?.length ?? 0) > 0 ? (
          <section className="rounded-2xl border border-stone-100 bg-white p-4 shadow-sm">
            <p className="text-sm font-bold text-stone-900">История Амов</p>
            <ul className="mt-3 space-y-2">
              {data.ama_transactions?.map((tx) => (
                <li
                  key={tx.id}
                  className="flex items-start justify-between gap-2 border-b border-stone-50 pb-2 text-sm last:border-0 last:pb-0"
                >
                  <div className="min-w-0">
                    <p className="font-medium text-stone-900">{tx.user_name}</p>
                    <p className="text-xs text-stone-500">{tx.reason_label}</p>
                  </div>
                  <span className="shrink-0 font-semibold text-red-700">
                    {tx.amount} Ам
                  </span>
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        <section className="rounded-2xl border border-stone-100 bg-white p-4 shadow-sm">
          <p className="text-sm font-bold text-stone-900">Что такое Амы</p>
          <p className="mt-2 text-sm leading-relaxed text-stone-600">
            Амы — внутренний ресурс ПланАм для дополнительных AI-действий: вопрос
            нутрициологу, разбор чека, голос, глубокий анализ. Просмотр меню,
            покупок и запасов Амы не тратит.
          </p>
          <ul className="mt-3 space-y-1 text-xs text-stone-500">
            {Object.entries(data.ama_costs).slice(0, 5).map(([key, cost]) => (
              <li key={key} className="flex justify-between gap-2">
                <span>{AMA_ACTION_LABELS[key] ?? key}</span>
                <span className="font-medium text-stone-700">
                  {formatAmaCost(cost)}
                </span>
              </li>
            ))}
          </ul>
        </section>

        <section>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-stone-500">
            Тарифы
          </p>
          <ul className="space-y-2">
            {data.plans.map((plan) => {
              const isCurrent = plan.is_current;
              return (
                <li
                  key={plan.code}
                  className={`rounded-2xl border p-4 ${
                    isCurrent
                      ? "border-emerald-200 bg-emerald-50/40"
                      : "border-stone-100 bg-white"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="font-bold text-stone-900">{plan.name}</p>
                      <p className="text-sm text-stone-500">
                        {planPriceLabel(plan.price_rub)}
                      </p>
                    </div>
                    {isCurrent ? (
                      <span className="rounded-full bg-emerald-600 px-2 py-0.5 text-xs font-semibold text-white">
                        Сейчас
                      </span>
                    ) : null}
                  </div>
                  <ul className="mt-2 space-y-0.5 text-sm text-stone-600">
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
                      className="mt-3 w-full rounded-xl border border-stone-200 py-2.5 text-sm font-semibold text-stone-800 disabled:opacity-50"
                    >
                      {selecting === plan.code ? "…" : "Выбрать тариф"}
                    </button>
                  ) : null}
                </li>
              );
            })}
          </ul>
          <p className="mt-2 px-1 text-xs text-stone-500">
            Оплата пока не подключена — выбор тарифа для теста без списания.
          </p>
        </section>

        <section className="rounded-2xl border border-dashed border-amber-200 bg-amber-50/30 p-4">
          <p className="font-semibold text-stone-900">Купить Амы</p>
          <p className="mt-1 text-sm text-stone-600">
            Пополнение баланса появится в следующем обновлении.
          </p>
          <button
            type="button"
            disabled
            className="mt-3 w-full rounded-xl bg-stone-200 py-2.5 text-sm font-semibold text-stone-500"
          >
            Скоро
          </button>
        </section>
    </ScreenLayout>
  );
}
