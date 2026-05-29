"use client";

import Link from "next/link";

import { formatGoodsCount, formatProductsCount } from "@/lib/home/plan-summary";

type MealRow = { label: string; name: string };

type HomeTodayCardProps = {
  loading: boolean;
  hasPlan: boolean;
  mealRows: MealRow[];
  personsCount: number;
  toBuy: number;
  pantryUsed: number;
};

/**
 * Блок «Сегодня» — главный ответ на «что важно сегодня»: план дня + краткая
 * сводка и переходы. Деталь живёт в разделе «Меню».
 */
export function HomeTodayCard({
  loading,
  hasPlan,
  mealRows,
  personsCount,
  toBuy,
  pantryUsed,
}: HomeTodayCardProps) {
  if (loading) {
    return (
      <section
        className="animate-pulse rounded-3xl border border-stone-100 bg-white p-5 shadow-sm"
        aria-busy="true"
      >
        <div className="h-3 w-28 rounded bg-stone-100" />
        <div className="mt-4 space-y-2">
          <div className="h-4 w-full rounded bg-stone-100" />
          <div className="h-4 w-[85%] rounded bg-stone-100" />
          <div className="h-4 w-[60%] rounded bg-stone-100" />
        </div>
      </section>
    );
  }

  if (!hasPlan) {
    return (
      <section className="rounded-3xl border border-stone-100 bg-white p-4 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-wide text-stone-400">
          План на сегодня
        </p>
        <h2 className="mt-2 text-lg font-bold text-stone-900">Плана пока нет</h2>
        <p className="mt-1 text-sm text-stone-500">
          Соберите его — ПланАм подскажет, что приготовить и купить.
        </p>
        <Link
          href="/menu"
          className="mt-4 flex min-h-[44px] w-full items-center justify-center rounded-xl bg-emerald-600 px-4 py-3 text-sm font-semibold text-white shadow-md shadow-emerald-200/50 transition active:scale-[0.99]"
        >
          Составить меню
        </Link>
      </section>
    );
  }

  return (
    <section className="rounded-3xl border border-emerald-100 bg-gradient-to-b from-emerald-50/70 to-white p-4 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
        Сегодня в плане
      </p>
      <ul className="mt-3 space-y-2">
        {mealRows.map((row) => (
          <li
            key={row.label}
            className="flex items-baseline justify-between gap-2 text-sm"
          >
            <span className="shrink-0 font-medium text-stone-500">
              {row.label}
            </span>
            <span className="min-w-0 truncate text-right font-semibold text-stone-900">
              {row.name}
            </span>
          </li>
        ))}
      </ul>

      <ul className="mt-4 space-y-1.5 border-t border-emerald-100/80 pt-3 text-sm text-stone-600">
        <li className="flex justify-between gap-2">
          <span>Рассчитано на</span>
          <span className="font-medium text-stone-800">
            {personsCount} {personsCount === 1 ? "человека" : "человек"}
          </span>
        </li>
        <li className="flex justify-between gap-2">
          <span>Купить</span>
          <span className="font-medium text-stone-800">
            {formatGoodsCount(toBuy)}
          </span>
        </li>
        <li className="flex justify-between gap-2">
          <span>Из запасов</span>
          <span className="font-medium text-stone-800">
            {formatProductsCount(pantryUsed)}
          </span>
        </li>
      </ul>

      <div className="mt-4 grid grid-cols-2 gap-2">
        <Link
          href="/menu"
          className="flex min-h-[44px] items-center justify-center rounded-xl bg-emerald-600 px-3 py-2.5 text-center text-sm font-semibold text-white shadow-sm transition active:scale-[0.99]"
        >
          Открыть план
        </Link>
        <Link
          href="/shopping"
          className="flex min-h-[44px] items-center justify-center rounded-xl border border-emerald-200 bg-white px-3 py-2.5 text-center text-sm font-semibold text-emerald-800 transition active:scale-[0.99]"
        >
          Открыть покупки
        </Link>
      </div>
    </section>
  );
}
