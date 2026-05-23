"use client";

import Link from "next/link";

import { BottomBackButton } from "@/components/layout/BottomBackButton";
import {
  formatAmasBalance,
  getProfileBilling,
} from "@/lib/profile/billing";

const PLANS = [
  {
    id: "personal",
    name: "Личный",
    desc: "Один профиль, полный цикл питания и покупок",
  },
  {
    id: "shared",
    name: "Совместный",
    desc: "Два человека с общим контекстом",
  },
  {
    id: "family",
    name: "Семейный",
    desc: "Семья и виртуальные участники",
  },
  {
    id: "pro",
    name: "ПланАм PRO",
    desc: "Спорт, здоровье, вес и аналитика",
  },
] as const;

export default function SubscriptionPage() {
  const billing = getProfileBilling();

  return (
    <div className="min-h-screen bg-stone-50">
      <header className="bg-white px-4 pb-2 pt-7 sm:px-5">
        <div className="mx-auto max-w-lg">
          <h1 className="text-2xl font-bold text-stone-900">Подписка и Амы</h1>
          <p className="mt-1 text-sm text-stone-500">Тариф и AI-действия</p>
        </div>
      </header>

      <main className="mx-auto max-w-lg space-y-4 px-4 pb-4 pt-4 sm:px-5">
        <section className="rounded-3xl border border-amber-100 bg-gradient-to-br from-amber-50 to-white p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wide text-amber-800">
            Ваш баланс
          </p>
          <p className="mt-2 text-3xl font-bold text-amber-950">
            {formatAmasBalance(billing.amasBalance)}
          </p>
          <p className="mt-2 text-sm leading-relaxed text-stone-600">
            Амы тратятся на генерацию меню, разбор чеков и другие AI-действия.
            Пополнение и оплата появятся в следующих обновлениях.
          </p>
        </section>

        <section className="rounded-3xl border border-stone-100 bg-white p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wide text-stone-400">
            Текущий тариф
          </p>
          <p className="mt-1.5 text-xl font-bold text-stone-900">
            {billing.planLabel}
          </p>
        </section>

        <section>
          <p className="mb-2 px-1 text-xs font-semibold uppercase tracking-wide text-stone-400">
            Доступные тарифы
          </p>
          <ul className="space-y-2">
            {PLANS.map((plan) => {
              const isCurrent = plan.id === billing.planId;
              return (
                <li
                  key={plan.id}
                  className={`rounded-2xl border p-4 ${
                    isCurrent
                      ? "border-emerald-200 bg-emerald-50/50"
                      : "border-stone-100 bg-white"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <p className="font-semibold text-stone-900">{plan.name}</p>
                    {isCurrent ? (
                      <span className="shrink-0 rounded-full bg-emerald-600 px-2.5 py-0.5 text-xs font-semibold text-white">
                        Сейчас
                      </span>
                    ) : (
                      <span className="shrink-0 text-xs font-medium text-stone-400">
                        Скоро
                      </span>
                    )}
                  </div>
                  <p className="mt-1 text-sm text-stone-600">{plan.desc}</p>
                </li>
              );
            })}
          </ul>
        </section>

        <p className="text-center text-sm text-stone-500">
          <Link href="/profile" className="font-semibold text-emerald-700">
            ← В профиль
          </Link>
        </p>
      </main>

      <BottomBackButton className="pb-2 pt-2" />
    </div>
  );
}
