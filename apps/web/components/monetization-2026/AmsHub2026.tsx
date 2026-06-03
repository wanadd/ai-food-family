"use client";

import Link from "next/link";
import { useEffect } from "react";

import { Card2026 } from "@/components/planam-2026/ui/Card2026";
import { EmptyState2026 } from "@/components/planam-2026/ui/EmptyState2026";
import { Skeleton2026 } from "@/components/planam-2026/ui/Skeleton2026";
import { useSubscriptionOverview } from "@/components/subscription/SubscriptionProvider";
import { useTelegram } from "@/components/TelegramProvider";
import { MONETIZATION_PATHS } from "@/lib/monetization/paths";
import { formatAmasBalance } from "@/lib/profile/billing";
import { AMA_ACTION_LABELS, formatAmaCost } from "@/lib/subscription/ama";

export function AmsHub2026() {
  const { initData, isTelegram } = useTelegram();
  const { overview: data, loading, ensureLoaded } = useSubscriptionOverview();

  useEffect(() => {
    if (initData) {
      ensureLoaded();
    }
  }, [initData, ensureLoaded]);

  if (!initData && !isTelegram && !loading) {
    return (
      <p className="px-4 py-16 text-center pa26-body text-pa-muted">
        Баланс доступен в Telegram Mini App
      </p>
    );
  }

  if (loading || !data) {
    return (
      <div className="space-y-3 px-4 py-6">
        <Skeleton2026 variant="rect" className="h-24 w-full" />
        <Skeleton2026 variant="rect" className="h-40 w-full" />
      </div>
    );
  }

  const transactions = data.ama_transactions ?? [];
  const costEntries = Object.entries(data.ama_costs ?? {});

  return (
    <div className="space-y-4 px-4 pb-8 pt-2">
      <Card2026 className="border-sage-200 bg-sage-50/50 dark:border-sage-700/40 dark:bg-sage-700/15">
        <p className="pa26-micro text-pa-muted">
          {data.is_family_billing ? "Баланс семьи" : "Ваш баланс"}
        </p>
        <p className="pa26-page-title mt-1 tabular-nums">
          {formatAmasBalance(data.ama_balance)}
        </p>
        {data.is_family_billing && !data.can_spend_ama ? (
          <p className="pa26-caption mt-2 text-pa-muted">
            Тратить Амы может администратор семьи
          </p>
        ) : null}
        <Link
          href={MONETIZATION_PATHS.subscription}
          className="mt-3 inline-block pa26-micro font-semibold text-sage-700 dark:text-sage-300"
        >
          Тарифы и пополнение →
        </Link>
      </Card2026>

      <section>
        <h2 className="pa26-section-title">На что тратятся</h2>
        <p className="pa26-caption mb-3 text-pa-muted">
          Просмотр меню и покупок Амы не расходует
        </p>
        <ul className="space-y-2 rounded-card border border-pa-border bg-pa-surface p-4 dark:shadow-none">
          {costEntries.map(([key, cost]) => (
            <li
              key={key}
              className="flex items-center justify-between gap-2 pa26-caption"
            >
              <span className="text-pa-muted">
                {AMA_ACTION_LABELS[key] ?? key}
              </span>
              <span className="font-semibold tabular-nums">
                {formatAmaCost(cost)}
              </span>
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2 className="pa26-section-title">История</h2>
        {transactions.length === 0 ? (
          <EmptyState2026
            title="Пока без списаний"
            description="Когда воспользуетесь AI — заменой блюда или вопросом нутрициологу — история появится здесь."
          />
        ) : (
          <ul className="space-y-2 rounded-card border border-pa-border bg-pa-surface p-4">
            {transactions.map((tx) => (
              <li
                key={tx.id}
                className="flex items-start justify-between gap-2 border-b border-pa-border pb-2 last:border-0 last:pb-0"
              >
                <div className="min-w-0">
                  <p className="pa26-caption font-medium">{tx.reason_label}</p>
                  <p className="pa26-micro text-pa-muted">{tx.user_name}</p>
                </div>
                <span className="shrink-0 font-semibold tabular-nums text-pa-error">
                  {tx.amount} Ам
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <Card2026 className="border-dashed opacity-90">
        <p className="pa26-card-title">Докупка Амов</p>
        <p className="pa26-caption mt-1 text-pa-muted">
          Пакеты S / M / L появятся вместе с оплатой — пока баланс пополняется по
          тарифу.
        </p>
        <p className="mt-3 rounded-control bg-cream-deep px-3 py-2 text-center pa26-micro font-semibold text-pa-muted dark:bg-graphite-700/40">
          Скоро
        </p>
      </Card2026>
    </div>
  );
}
