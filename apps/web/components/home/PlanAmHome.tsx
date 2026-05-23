"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { useTelegram } from "@/components/TelegramProvider";
import {
  countExpiringSoon,
  countPantryMatches,
  countToBuy,
  formatGoodsCount,
  formatPersonsLabel,
  formatProductsCount,
  getMealRows,
  getPersonsCount,
} from "@/lib/home/plan-summary";
import { fetchSelectedMenu } from "@/lib/menu/api";
import type { SelectedMenu } from "@/lib/menu/types";
import { fetchPantry } from "@/lib/pantry/api";
import type { PantryList } from "@/lib/pantry/types";
import { fetchShoppingList } from "@/lib/shopping/api";
import type { ShoppingList } from "@/lib/shopping/types";

function ProfileIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className="h-5 w-5 text-stone-600"
      aria-hidden
    >
      <circle cx="12" cy="8" r="4" stroke="currentColor" strokeWidth="1.75" />
      <path
        d="M5 20c0-3.314 3.134-6 7-6s7 2.686 7 6"
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function PlanAmHome() {
  const { initData } = useTelegram();
  const { mode, context, loading: modeLoading } = useAppMode();

  const [loading, setLoading] = useState(true);
  const [selectedMenu, setSelectedMenu] = useState<SelectedMenu | null>(null);
  const [shopping, setShopping] = useState<ShoppingList | null>(null);
  const [pantry, setPantry] = useState<PantryList | null>(null);

  const loadHomeData = useCallback(async () => {
    if (!initData) {
      setLoading(false);
      setSelectedMenu(null);
      setShopping(null);
      setPantry(null);
      return;
    }

    setLoading(true);
    try {
      const [selected, list, pantryList] = await Promise.all([
        fetchSelectedMenu(initData, mode),
        fetchShoppingList(initData, mode).catch(() => null),
        fetchPantry(initData, mode).catch(() => null),
      ]);
      setSelectedMenu(selected);
      setShopping(list);
      setPantry(pantryList);
    } finally {
      setLoading(false);
    }
  }, [initData, mode]);

  useEffect(() => {
    if (modeLoading) {
      setLoading(true);
      return;
    }
    void loadHomeData();
  }, [loadHomeData, modeLoading]);

  const hasPlan = Boolean(selectedMenu?.menu);
  const mealRows = useMemo(
    () => (selectedMenu ? getMealRows(selectedMenu.menu) : []),
    [selectedMenu],
  );

  const personsCount = getPersonsCount(mode, context);
  const toBuy = countToBuy(shopping);
  const pantryUsed = countPantryMatches(
    selectedMenu?.menu ?? null,
    pantry?.items ?? [],
  );
  const pantryTotal = pantry?.active_count ?? pantry?.items.length ?? 0;
  const expiringSoon = countExpiringSoon(pantry?.items ?? []);

  const isFamily = mode === "family" && context?.family;
  const isBusy = loading || modeLoading;

  return (
    <div className="min-h-screen bg-stone-50">
      <div className="mx-auto max-w-lg px-4 pb-4 pt-5 sm:px-5">
        <header className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h1 className="text-[1.65rem] font-bold leading-tight text-stone-900">
              ПланАм
            </h1>
            <p className="mt-0.5 text-sm leading-snug text-stone-500">
              Умный план питания и покупок
            </p>
          </div>
          <Link
            href="/profile"
            aria-label="Профиль"
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-stone-200 bg-white shadow-sm transition hover:border-emerald-200 hover:bg-emerald-50"
          >
            <ProfileIcon />
          </Link>
        </header>

        <main className="mt-4 space-y-3">
          <section className="rounded-2xl border border-stone-100 bg-white px-4 py-3 shadow-sm">
            {isFamily ? (
              <>
                <p className="text-sm font-semibold text-stone-900">
                  Семья: {context.family!.name}
                </p>
                <p className="mt-0.5 text-sm text-stone-500">
                  {context.family!.members_count}{" "}
                  {context.family!.members_count === 1
                    ? "участник"
                    : context.family!.members_count >= 2 &&
                        context.family!.members_count <= 4
                      ? "участника"
                      : "участников"}
                </p>
              </>
            ) : (
              <p className="text-sm font-semibold text-stone-900">
                {formatPersonsLabel(personsCount)}
              </p>
            )}
          </section>

          {isBusy ? (
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
          ) : hasPlan ? (
            <>
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
                      {personsCount}{" "}
                      {personsCount === 1 ? "человека" : "человек"}
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
            </>
          ) : (
            <section className="rounded-3xl border border-stone-100 bg-white p-4 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-wide text-stone-400">
                План на сегодня
              </p>
              <h2 className="mt-2 text-lg font-bold text-stone-900">
                План питания ещё не создан
              </h2>
              <p className="mt-1 text-sm text-stone-500">
                Соберите меню в разделе «Меню»
              </p>
              <Link
                href="/menu"
                className="mt-4 flex min-h-[44px] w-full items-center justify-center rounded-xl bg-emerald-600 px-4 py-3 text-sm font-semibold text-white shadow-md shadow-emerald-200/50 transition active:scale-[0.99]"
              >
                Составить план
              </Link>
            </section>
          )}

          <section className="rounded-2xl border border-stone-100 bg-white p-4 shadow-sm">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-stone-400">
                  Запасы
                </p>
                <p className="mt-1.5 text-sm text-stone-700">
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
                href="/pantry"
                className="shrink-0 rounded-xl bg-stone-100 px-3 py-2 text-xs font-semibold text-stone-700 transition hover:bg-emerald-50 hover:text-emerald-800"
              >
                Открыть
              </Link>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}
