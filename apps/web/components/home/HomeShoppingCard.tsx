"use client";

import Link from "next/link";

import { formatGoodsCount, formatProductsCount } from "@/lib/home/plan-summary";

type HomeShoppingCardProps = {
  toBuy: number;
  pantryTotal: number;
  expiringSoon: number;
};

/**
 * Блок «Что купить» — короткий ответ на вопрос покупок: сколько докупить,
 * сколько в запасах и что скоро заканчивается. Источники уже загружены на
 * Home (shopping + pantry), без новых запросов.
 */
export function HomeShoppingCard({
  toBuy,
  pantryTotal,
  expiringSoon,
}: HomeShoppingCardProps) {
  return (
    <section className="rounded-2xl border border-stone-100 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase tracking-wide text-stone-400">
            Что купить
          </p>
          <p className="mt-1.5 text-sm text-stone-700">
            {toBuy > 0 ? (
              <>
                Осталось купить{" "}
                <span className="font-semibold text-stone-900">
                  {formatGoodsCount(toBuy)}
                </span>
              </>
            ) : (
              "Всё куплено — список пуст"
            )}
          </p>
        </div>
        <Link
          href="/shopping"
          className="shrink-0 rounded-xl bg-emerald-600 px-3 py-2 text-xs font-semibold text-white transition active:scale-[0.98]"
        >
          Открыть
        </Link>
      </div>

      <div className="mt-3 flex items-start justify-between gap-3 border-t border-stone-100 pt-3">
        <div className="min-w-0">
          <p className="text-sm text-stone-700">
            {formatProductsCount(pantryTotal)} в запасах
          </p>
          <p className="mt-0.5 text-sm text-stone-500">
            Скоро заканчиваются:{" "}
            <span
              className={
                expiringSoon > 0
                  ? "font-semibold text-amber-700"
                  : "font-medium text-stone-600"
              }
            >
              {expiringSoon}
            </span>
          </p>
        </div>
        <Link
          href="/shopping/pantry"
          className="shrink-0 rounded-xl bg-stone-100 px-3 py-2 text-xs font-semibold text-stone-700 transition hover:bg-emerald-50 hover:text-emerald-800"
        >
          Запасы
        </Link>
      </div>
    </section>
  );
}
