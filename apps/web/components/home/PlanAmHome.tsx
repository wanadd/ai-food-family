"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { useTelegram } from "@/components/TelegramProvider";
import {
  cacheKey,
  fetchOrCache,
  getCached as getCachedOrNull,
} from "@/lib/cache/session-cache";
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
import { fetchNutritionProfile } from "@/lib/nutrition-profile/api";
import type { NutritionProfileData } from "@/lib/nutrition-profile/types";
import { fetchPantry } from "@/lib/pantry/api";
import type { PantryList } from "@/lib/pantry/types";
import {
  getNutritionProfileProgress,
} from "@/lib/profile/nutrition-summary";
import { fetchShoppingList } from "@/lib/shopping/api";
import type { ShoppingList } from "@/lib/shopping/types";

const PREFETCH_TABS = ["/menu", "/shopping", "/pantry", "/nutritionist"];

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
  const router = useRouter();
  const { initData } = useTelegram();
  const { mode, context, loading: modeLoading } = useAppMode();

  // Initialise from session cache so a return visit renders instantly.
  const cachedSelectedMenu = initData
    ? getCachedOrNull<SelectedMenu>(cacheKey.selectedMenu(mode))
    : null;
  const cachedShopping = initData
    ? getCachedOrNull<ShoppingList>(cacheKey.shoppingList(mode))
    : null;
  const cachedPantry = initData
    ? getCachedOrNull<PantryList>(cacheKey.pantry(mode))
    : null;
  const cachedProfile = initData
    ? getCachedOrNull<NutritionProfileData>(cacheKey.nutritionProfile())
    : null;

  const [menuLoading, setMenuLoading] = useState(
    Boolean(initData) && cachedSelectedMenu == null,
  );
  const [selectedMenu, setSelectedMenu] = useState<SelectedMenu | null>(
    cachedSelectedMenu,
  );
  const [shopping, setShopping] = useState<ShoppingList | null>(cachedShopping);
  const [pantry, setPantry] = useState<PantryList | null>(cachedPantry);
  const [nutritionProfile, setNutritionProfile] =
    useState<NutritionProfileData | null>(cachedProfile);
  const [profileLoaded, setProfileLoaded] = useState(cachedProfile != null);

  useEffect(() => {
    if (modeLoading) {
      setMenuLoading(true);
      return;
    }
    if (!initData) {
      setMenuLoading(false);
      setSelectedMenu(null);
      setShopping(null);
      setPantry(null);
      setNutritionProfile(null);
      setProfileLoaded(false);
      return;
    }

    let cancelled = false;

    const primed = getCachedOrNull<SelectedMenu>(cacheKey.selectedMenu(mode));
    if (primed != null) {
      setSelectedMenu(primed);
      setMenuLoading(false);
    } else {
      setMenuLoading(true);
    }

    void fetchOrCache(cacheKey.selectedMenu(mode), () =>
      fetchSelectedMenu(initData, mode),
    )
      .then((selected) => {
        if (cancelled) return;
        setSelectedMenu(selected);
      })
      .catch(() => {
        if (cancelled) return;
        setSelectedMenu(null);
      })
      .finally(() => {
        if (cancelled) return;
        setMenuLoading(false);
      });

    void fetchOrCache(cacheKey.shoppingList(mode), async () => {
      const list = await fetchShoppingList(initData, mode);
      return list;
    })
      .then((list) => {
        if (cancelled) return;
        setShopping(list);
      })
      .catch(() => {
        if (cancelled) return;
        setShopping(null);
      });

    void fetchOrCache(cacheKey.pantry(mode), async () => {
      const list = await fetchPantry(initData, mode);
      return list;
    })
      .then((pantryList) => {
        if (cancelled) return;
        setPantry(pantryList);
      })
      .catch(() => {
        if (cancelled) return;
        setPantry(null);
      });

    if (cachedProfile == null) {
      setProfileLoaded(false);
    }
    void fetchOrCache(cacheKey.nutritionProfile(), async () => {
      const profile = await fetchNutritionProfile(initData);
      return profile;
    })
      .then((profile) => {
        if (cancelled) return;
        setNutritionProfile(profile);
      })
      .catch(() => {
        if (cancelled) return;
        setNutritionProfile(null);
      })
      .finally(() => {
        if (cancelled) return;
        setProfileLoaded(true);
      });

    return () => {
      cancelled = true;
    };
    // cachedProfile only read at mount; intentionally not in deps.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initData, mode, modeLoading]);

  // Warm the JS chunks for the bottom tabs after first paint so the next
  // tap navigates without a network round-trip for the route bundle.
  useEffect(() => {
    if (!initData) return;
    for (const path of PREFETCH_TABS) {
      router.prefetch(path);
    }
  }, [initData, router]);

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
  const isBusy = menuLoading || modeLoading;

  const profileProgress = nutritionProfile
    ? getNutritionProfileProgress(nutritionProfile)
    : 0;
  const profileNeedsAttention =
    profileLoaded && nutritionProfile != null && profileProgress < 80;

  // A short, state-driven subtitle that replaces the static slogan.
  // Examples:
  //   "Меню готово · купить 4 · 2 заканчиваются"
  //   "Меню готово · всё уже в запасах"
  //   "Плана пока нет — соберите его за минуту"
  const subtitleParts: string[] = [];
  if (isBusy) {
    subtitleParts.push("Готовим сводку…");
  } else if (hasPlan) {
    subtitleParts.push("Меню готово");
    if (toBuy > 0) {
      subtitleParts.push(`купить ${formatGoodsCount(toBuy)}`);
    } else if (pantryUsed > 0) {
      subtitleParts.push("всё уже в запасах");
    }
    if (expiringSoon > 0) {
      subtitleParts.push(`${expiringSoon} заканчиваются`);
    }
  } else {
    subtitleParts.push("Плана пока нет — соберите за минуту");
  }
  const heroSubtitle = subtitleParts.join(" · ");

  return (
    <div className="min-h-screen bg-stone-50">
      <div className="mx-auto max-w-lg px-4 pb-4 pt-5 sm:px-5">
        <header className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h1 className="text-[1.65rem] font-bold leading-tight text-stone-900">
              ПланАм
            </h1>
            <p className="mt-0.5 text-sm leading-snug text-stone-500">
              {heroSubtitle}
            </p>
            {isFamily ? (
              <p className="mt-0.5 text-xs text-stone-400">
                Семья: {context.family!.name}
              </p>
            ) : personsCount > 1 ? (
              <p className="mt-0.5 text-xs text-stone-400">
                {formatPersonsLabel(personsCount)}
              </p>
            ) : null}
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

          {profileNeedsAttention ? (
            <Link
              href="/profile/nutrition"
              className="flex items-start justify-between gap-3 rounded-2xl border border-emerald-100 bg-emerald-50/60 px-4 py-3 shadow-sm transition active:scale-[0.99]"
            >
              <div className="min-w-0">
                <p className="text-sm font-semibold text-stone-900">
                  Можно дополнить профиль
                </p>
                <p className="mt-0.5 text-xs text-stone-600">
                  Заполнено {profileProgress}%. Если хотите —
                  меню и советы станут точнее.
                </p>
              </div>
              <span
                className="shrink-0 self-center rounded-full bg-white px-2.5 py-1 text-xs font-semibold text-emerald-800"
                aria-hidden
              >
                Открыть
              </span>
            </Link>
          ) : null}

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
                Плана пока нет
              </h2>
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
