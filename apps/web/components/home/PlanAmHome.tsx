"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { useTelegram } from "@/components/TelegramProvider";
import { HomeAskPlanAm } from "@/components/home/HomeAskPlanAm";
import { HomeQuickActions } from "@/components/home/HomeQuickActions";
import { HomeShoppingCard } from "@/components/home/HomeShoppingCard";
import { HomeTodayCard } from "@/components/home/HomeTodayCard";
import { NutritionistAdviceCard } from "@/components/nutritionist/NutritionistAdviceCard";
import {
  cacheKey,
  fetchOrCache,
  getCached as getCachedOrNull,
  invalidate,
} from "@/lib/cache/session-cache";
import {
  countExpiringSoon,
  countPantryMatches,
  countToBuy,
  formatGoodsCount,
  formatPersonsLabel,
  getMealRows,
  getPersonsCount,
} from "@/lib/home/plan-summary";
import { fetchSelectedMenu } from "@/lib/menu/api";
import type { SelectedMenu } from "@/lib/menu/types";
import { pickMainAdvice } from "@/lib/nutritionist/main-advice";
import { fetchNutritionProfile } from "@/lib/nutrition-profile/api";
import type { NutritionProfileData } from "@/lib/nutrition-profile/types";
import { fetchPantry } from "@/lib/pantry/api";
import type { PantryList } from "@/lib/pantry/types";
import { getNutritionProfileProgress } from "@/lib/profile/nutrition-summary";
import { fetchShoppingList } from "@/lib/shopping/api";
import type { ShoppingList } from "@/lib/shopping/types";

// Блоки 5–6 грузим лениво, чтобы не замедлять первый экран Home.
const HomeFamilySummary = dynamic(
  () =>
    import("@/components/home/HomeFamilySummary").then(
      (m) => m.HomeFamilySummary,
    ),
  { ssr: false },
);
const HomeRecommendations = dynamic(
  () =>
    import("@/components/home/HomeRecommendations").then(
      (m) => m.HomeRecommendations,
    ),
  { ssr: false, loading: () => null },
);

const PREFETCH_TABS = ["/menu", "/shopping", "/health", "/profile"];

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

    void fetchOrCache(cacheKey.shoppingList(mode), () =>
      fetchShoppingList(initData, mode),
    )
      .then((list) => {
        if (cancelled) return;
        setShopping(list);
      })
      .catch(() => {
        if (cancelled) return;
        setShopping(null);
      });

    void fetchOrCache(cacheKey.pantry(mode), () => fetchPantry(initData, mode))
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
    void fetchOrCache(cacheKey.nutritionProfile(), () =>
      fetchNutritionProfile(initData),
    )
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

  // Re-fetch plan/shopping/pantry after a quick action mutated the active plan.
  const refreshPlanData = useCallback(() => {
    if (!initData) return;
    invalidate(cacheKey.selectedMenu(mode));
    invalidate(cacheKey.shoppingList(mode));
    invalidate(cacheKey.pantry(mode));
    void fetchOrCache(cacheKey.selectedMenu(mode), () =>
      fetchSelectedMenu(initData, mode),
    )
      .then(setSelectedMenu)
      .catch(() => {});
    void fetchOrCache(cacheKey.shoppingList(mode), () =>
      fetchShoppingList(initData, mode),
    )
      .then(setShopping)
      .catch(() => {});
    void fetchOrCache(cacheKey.pantry(mode), () => fetchPantry(initData, mode))
      .then(setPantry)
      .catch(() => {});
  }, [initData, mode]);

  // Warm the JS chunks for the bottom tabs after first paint.
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

  const familyName = context?.family?.name ?? null;
  const isFamily = mode === "family" && Boolean(context?.family);
  const isBusy = menuLoading || modeLoading;

  const profileProgress = nutritionProfile
    ? getNutritionProfileProgress(nutritionProfile)
    : 0;
  const profileNeedsAttention =
    profileLoaded && nutritionProfile != null && profileProgress < 80;

  // Совет ПланАм — клиентский deterministic (без AI-запроса на Home).
  const advice = useMemo(
    () =>
      pickMainAdvice({
        profile: nutritionProfile,
        menu: selectedMenu?.menu ?? null,
        pantry,
        pantryActiveCount: pantry?.active_count ?? 0,
      }),
    [nutritionProfile, selectedMenu, pantry],
  );

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
            {isFamily && familyName ? (
              <p className="mt-0.5 text-xs text-stone-400">
                Семья: {familyName}
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
                  Заполнено {profileProgress}%. Если хотите — меню и советы
                  станут точнее.
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

          {/* 1. Сегодня */}
          <HomeTodayCard
            loading={isBusy}
            hasPlan={hasPlan}
            mealRows={mealRows}
            personsCount={personsCount}
            toBuy={toBuy}
            pantryUsed={pantryUsed}
          />

          {/* 2. Что купить */}
          <HomeShoppingCard
            toBuy={toBuy}
            pantryTotal={pantryTotal}
            expiringSoon={expiringSoon}
          />

          {/* 3. Совет ПланАм (deterministic, без AI-запроса) */}
          {initData && profileLoaded ? (
            <NutritionistAdviceCard
              advice={advice}
              initData={initData}
              mode={mode}
            />
          ) : null}

          {/* 4. Спросить ПланАм (AI-хаб → чат) */}
          <HomeAskPlanAm />

          {/* 5. Быстрые действия (только при активном плане) */}
          {initData && hasPlan ? (
            <HomeQuickActions
              initData={initData}
              mode={mode}
              onApplied={refreshPlanData}
            />
          ) : null}

          {/* 6. Сводка семьи (family mode, лениво) */}
          {isFamily ? <HomeFamilySummary /> : null}

          {/* 7. Рекомендации (лениво) */}
          {initData ? <HomeRecommendations /> : null}
        </main>
      </div>
    </div>
  );
}
