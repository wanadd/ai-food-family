"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { useTelegram } from "@/components/TelegramProvider";
import { fetchSelectedMenu } from "@/lib/menu/api";
import type { SelectedMenu } from "@/lib/menu/types";
import { fetchNutritionProfile } from "@/lib/nutrition-profile/api";
import { isNutritionProfileComplete } from "@/lib/profile/nutrition-summary";
import { fetchShoppingList } from "@/lib/shopping/api";
import type { ShoppingList } from "@/lib/shopping/types";

function formatUpdatedToday(iso: string | undefined): string {
  if (!iso) {
    return "Обновлён сегодня";
  }
  const date = new Date(iso);
  const now = new Date();
  if (date.toDateString() === now.toDateString()) {
    return "Обновлён сегодня";
  }
  return `Обновлён ${date.toLocaleDateString("ru-RU", { day: "numeric", month: "short" })}`;
}

function formatGoodsCount(count: number): string {
  const n = Math.abs(count);
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) {
    return `${n} товар`;
  }
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) {
    return `${n} товара`;
  }
  return `${n} товаров`;
}

function ProfileIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className="h-6 w-6 text-stone-600"
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
  const { initData, user } = useTelegram();
  const { mode, loading: modeLoading } = useAppMode();

  const [loadingSelectedMenu, setLoadingSelectedMenu] = useState(true);
  const [nutritionReady, setNutritionReady] = useState<boolean | null>(null);
  const [selectedMenu, setSelectedMenu] = useState<SelectedMenu | null>(null);
  const [shopping, setShopping] = useState<ShoppingList | null>(null);

  const displayName =
    user?.first_name?.trim() ||
    user?.username?.trim() ||
    "друг";

  const loadHomeData = useCallback(async () => {
    if (!initData) {
      setLoadingSelectedMenu(false);
      setNutritionReady(null);
      setSelectedMenu(null);
      setShopping(null);
      return;
    }

    setLoadingSelectedMenu(true);
    try {
      const [nutrition, selected, list] = await Promise.all([
        fetchNutritionProfile(initData).catch(() => null),
        fetchSelectedMenu(initData, mode),
        fetchShoppingList(initData, mode).catch(() => null),
      ]);
      setNutritionReady(isNutritionProfileComplete(nutrition));
      setSelectedMenu(selected);
      setShopping(list);
    } finally {
      setLoadingSelectedMenu(false);
    }
  }, [initData, mode]);

  useEffect(() => {
    if (modeLoading) {
      setLoadingSelectedMenu(true);
      return;
    }
    void loadHomeData();
  }, [loadHomeData, modeLoading]);

  const isCheckingMenu = loadingSelectedMenu || modeLoading;
  const planHref = nutritionReady ? "/menu" : "/profile/nutrition";
  const goodsCount = shopping?.total_count ?? 0;

  return (
    <div className="min-h-screen bg-white">
      <div className="mx-auto max-w-lg px-5 pb-6 pt-6">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <h1 className="text-[2rem] font-bold leading-tight tracking-tight text-stone-900">
              ПланАм
            </h1>
            <p className="mt-1 text-lg font-medium text-emerald-600">
              Питайся с умом
            </p>
          </div>
          <Link
            href="/profile"
            aria-label="Профиль"
            className="mt-1 flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-stone-200 bg-white shadow-sm transition hover:border-emerald-200 hover:bg-emerald-50"
          >
            <ProfileIcon />
          </Link>
        </div>

        <main className="mt-8 space-y-4">
          <section>
            <h2 className="text-2xl font-bold text-stone-900">
              Привет, {displayName}!
            </h2>
            <p className="mt-2 text-base leading-relaxed text-stone-600">
              Соберём меню, список покупок и план питания под ваши цели
            </p>
          </section>

          <section className="rounded-3xl border border-emerald-100 bg-gradient-to-b from-emerald-50/80 to-white p-5 shadow-sm">
            <Link
              href={planHref}
              className="flex w-full items-center justify-center rounded-2xl bg-emerald-600 py-4 text-lg font-semibold text-white shadow-md shadow-emerald-200/60 transition hover:bg-emerald-700 active:scale-[0.99]"
            >
              Составить план
            </Link>
            <p className="mt-3 text-center text-sm text-stone-500">
              Меню и покупки за ~30 секунд
            </p>
          </section>

          <section className="rounded-2xl border border-stone-100 bg-white p-4 shadow-sm">
            {isCheckingMenu ? (
              <div className="animate-pulse space-y-2" aria-busy="true">
                <div className="h-3 w-24 rounded bg-stone-100" />
                <div className="h-5 w-40 rounded bg-stone-100" />
              </div>
            ) : selectedMenu ? (
              <Link href="/menu" className="block">
                <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
                  Сегодня в плане
                </p>
                <h3 className="mt-1.5 text-lg font-bold leading-snug text-stone-900">
                  {selectedMenu.menu.title}
                </h3>
                <p className="mt-1 text-sm text-stone-500">Меню на день</p>
                <span className="mt-2.5 inline-flex rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-800">
                  Выбрано
                </span>
              </Link>
            ) : (
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-stone-400">
                  Сегодня в плане
                </p>
                <h3 className="mt-1.5 text-base font-semibold text-stone-800">
                  План питания ещё не создан
                </h3>
                <p className="mt-1 text-sm text-stone-500">
                  Нажмите «Составить план»
                </p>
              </div>
            )}
          </section>

          <section className="min-h-[7.5rem] rounded-2xl border border-stone-100 bg-white p-4 shadow-sm">
            <Link href="/shopping" className="flex h-full min-h-[5.5rem] flex-col justify-between">
              <p className="text-xs font-semibold uppercase tracking-wide text-amber-800">
                Список покупок
              </p>
              <div className="mt-2 flex flex-1 flex-col justify-center">
                <p className="text-2xl font-bold leading-tight text-stone-900">
                  {formatGoodsCount(goodsCount)}
                </p>
                <p className="mt-2 text-sm leading-normal text-stone-500">
                  {formatUpdatedToday(shopping?.updated_at)}
                </p>
              </div>
            </Link>
          </section>
        </main>
      </div>
    </div>
  );
}
