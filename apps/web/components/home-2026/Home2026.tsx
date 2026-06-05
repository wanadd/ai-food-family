"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import {
  LeftoversSheet2026,
  MealOutcomeSheet2026,
} from "@/components/dom-2026";
import { AIInsight2026 } from "@/components/home-2026/AIInsight2026";
import { HomeHero2026 } from "@/components/home-2026/HomeHero2026";
import { HomeQuickActions2026 } from "@/components/home-2026/HomeQuickActions2026";
import { HomeMonetizationBanner2026 } from "@/components/monetization-2026/HomeMonetizationBanner2026";
import { Button2026 } from "@/components/planam-2026/ui/Button2026";
import { useSubscriptionOverview } from "@/components/subscription/SubscriptionProvider";
import { buildHomeMonetizationBanner } from "@/lib/monetization/billing-status";
import { useTelegram } from "@/components/TelegramProvider";
import { EmptyState2026 } from "@/components/planam-2026/ui/EmptyState2026";
import {
  cacheKey,
  getCached,
  invalidate as invalidateCache,
  setCached,
} from "@/lib/cache/session-cache";
import {
  buildAiInsight,
  enrichTodayMeals,
  formatHomeDate,
  greetingFor,
  pickHeroMeal,
} from "@/lib/home/home-2026-data";
import { fetchMenuOverview } from "@/lib/menu/overview-api";
import type { MenuOverview } from "@/lib/menu/overview-types";
import { isPlanamUi2026Enabled } from "@/lib/planam/feature-flags";

type LoadState = "loading" | "ready" | "error";

export function Home2026() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { initData, user, isNewUser } = useTelegram();
  const { mode, loading: modeLoading, context } = useAppMode();
  const use2026 = isPlanamUi2026Enabled();
  const { overview: subscription, ensureLoaded: ensureSubscriptionLoaded } =
    useSubscriptionOverview();

  const cacheK = cacheKey.menuOverview(mode);
  const primed = initData ? getCached<MenuOverview>(cacheK) : null;

  const [overview, setOverview] = useState<MenuOverview | null>(primed);
  const [loadState, setLoadState] = useState<LoadState>(() =>
    primed ? "ready" : "loading",
  );
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [leftoversOpen, setLeftoversOpen] = useState(false);
  const [mealOutcomeOpen, setMealOutcomeOpen] = useState(false);

  const load = useCallback(
    async (force = false) => {
      if (!initData || modeLoading) {
        return;
      }
      const cached = getCached<MenuOverview>(cacheK);
      if (!force && cached) {
        setOverview(cached);
        setLoadState("ready");
        return;
      }
      setLoadState("loading");
      setErrorMessage(null);
      try {
        const data = await fetchMenuOverview(initData, mode);
        setCached(cacheK, data);
        setOverview(data);
        setLoadState("ready");
      } catch (err) {
        setLoadState("error");
        setErrorMessage(
          err instanceof Error ? err.message : "Не удалось загрузить данные",
        );
      }
    },
    [initData, mode, modeLoading, cacheK],
  );

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (initData && use2026) {
      ensureSubscriptionLoaded();
    }
  }, [initData, use2026, ensureSubscriptionLoaded]);

  useEffect(() => {
    if (searchParams.get("meal_outcome") === "1") {
      setMealOutcomeOpen(true);
      router.replace("/", { scroll: false });
    }
  }, [searchParams, router]);

  const hasMenu = Boolean(overview?.plan_summary.has_selected_menu);
  const meals = useMemo(
    () => (overview ? enrichTodayMeals(overview) : []),
    [overview],
  );
  const heroMeal = useMemo(() => pickHeroMeal(meals), [meals]);
  const insight = useMemo(
    () => (overview ? buildAiInsight(overview) : null),
    [overview],
  );
  const monetizationBanner = useMemo(
    () => (use2026 ? buildHomeMonetizationBanner(subscription) : null),
    [use2026, subscription],
  );

  const nextAction = overview?.next_action ?? null;
  const urgent =
    nextAction?.id === "use_pantry_item" ||
    (overview?.pantry_expiring_preview?.days_until_expiry ?? 99) <= 1;

  const healthInsight =
    overview?.nutritionist_advice.freshness_status !== "no_menu";

  const scopeLabel =
    mode === "family" && context?.family?.name
      ? context.family.name
      : "Личный";

  const handleMealOutcomeSuccess = useCallback(() => {
    invalidateCache(cacheK);
    void load(true);
  }, [cacheK, load]);

  const handleRetry = () => {
    invalidateCache(cacheK);
    void load(true);
  };

  const loading = loadState === "loading" || modeLoading;
  const [greeting] = useState(() => greetingFor(new Date()));
  const [dateLabel] = useState(() => formatHomeDate(new Date()));

  if (loadState === "error") {
    return (
      <div className="pb-4">
        <HomeHeader
          greeting={greeting}
          dateLabel={dateLabel}
          scopeLabel={scopeLabel}
          displayName={user?.first_name}
        />
        <EmptyState2026
          title="Не удалось обновить день"
          description={errorMessage ?? "Проверьте сеть и попробуйте снова."}
          actionLabel="Обновить"
          onAction={handleRetry}
        />
      </div>
    );
  }

  return (
    <div className="pb-2">
      <HomeHeader
        greeting={greeting}
        dateLabel={dateLabel}
        scopeLabel={scopeLabel}
        displayName={user?.first_name}
      />

      <HomeHero2026
        loading={loading}
        hasMenu={hasMenu}
        heroMeal={heroMeal}
        nextAction={nextAction}
        isNewUser={isNewUser}
        urgent={urgent}
      />

      {!loading ? (
        <HomeQuickActions2026 onLeftovers={() => setLeftoversOpen(true)} />
      ) : null}

      {!loading ? (
        <div className="flex gap-2 px-4 pt-3">
          <Button2026
            variant="primary"
            className="flex-1"
            onClick={() => router.push("/plan/today")}
          >
            Открыть меню
          </Button2026>
          <Button2026
            variant="secondary"
            className="flex-1"
            onClick={() => router.push("/home/shopping")}
          >
            Список покупок
          </Button2026>
        </div>
      ) : null}

      <HomeMonetizationBanner2026
        banner={monetizationBanner}
        loading={loading}
      />

      <AIInsight2026
        text={insight}
        loading={loading}
        healthRelated={healthInsight}
      />

      <LeftoversSheet2026
        open={leftoversOpen}
        onClose={() => setLeftoversOpen(false)}
      />
      <MealOutcomeSheet2026
        open={mealOutcomeOpen}
        onClose={() => setMealOutcomeOpen(false)}
        onSuccess={handleMealOutcomeSuccess}
      />
    </div>
  );
}

function HomeHeader({
  greeting,
  dateLabel,
  scopeLabel,
  displayName,
}: {
  greeting: string;
  dateLabel: string;
  scopeLabel: string;
  displayName?: string | null;
}) {
  return (
    <header className="px-4 pb-1 pt-[max(0.5rem,env(safe-area-inset-top))]">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="pa26-caption capitalize text-pa-muted">{dateLabel}</p>
          <h1 className="pa26-page-title mt-0.5 truncate">
            {greeting}
            {displayName ? `, ${displayName}` : ""} 👋
          </h1>
        </div>
        <span className="shrink-0 rounded-pill border border-pa-border bg-pa-surface px-3 py-1.5 pa26-micro font-semibold text-sage-700 dark:text-sage-300">
          {scopeLabel}
        </span>
      </div>
    </header>
  );
}
