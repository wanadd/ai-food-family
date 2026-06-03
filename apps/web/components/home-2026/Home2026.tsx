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
import { NextActionCard2026 } from "@/components/home-2026/NextActionCard2026";
import { PlanSnapshot2026 } from "@/components/home-2026/PlanSnapshot2026";
import { RecipeRail2026 } from "@/components/home-2026/RecipeRail2026";
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
  buildPlanSnapshot,
  enrichTodayMeals,
  formatHomeDate,
  greetingFor,
  pickHeroMeal,
} from "@/lib/home/home-2026-data";
import { resolveHomeRedirectPath } from "@/lib/home/redirect-path-2026";
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
  const snapshot = useMemo(
    () => (overview ? buildPlanSnapshot(overview) : []),
    [overview],
  );
  const insight = useMemo(
    () => (overview ? buildAiInsight(overview) : null),
    [overview],
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

  const handleCreateMenu = useCallback(() => {
    const path = nextAction?.redirect_path ?? "/menu/generate";
    router.push(resolveHomeRedirectPath(path, use2026, nextAction?.id));
  }, [nextAction, router, use2026]);

  const handleSnapshotClick = useCallback(
    (id: string) => {
      if (id === "shopping") {
        router.push("/home/shopping");
      } else if (id === "pantry") {
        router.push("/home/pantry");
      } else if (id === "leftovers") {
        setLeftoversOpen(true);
      }
    },
    [router],
  );

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
    <div className="pb-6">
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

      {!loading ? <NextActionCard2026 action={nextAction} /> : null}

      <PlanSnapshot2026
        items={snapshot}
        loading={loading}
        onItemClick={handleSnapshotClick}
      />

      {!loading && (overview?.meal_leftovers_count ?? 0) > 0 ? (
        <div className="px-4 pt-3">
          <button
            type="button"
            onClick={() => setLeftoversOpen(true)}
            className="w-full rounded-card border border-pa-border bg-pa-surface px-4 py-3 text-left shadow-soft transition active:scale-[0.98] dark:shadow-none"
          >
            <span className="pa26-card-title">Остатки дома</span>
            <span className="pa26-caption mt-0.5 block text-pa-muted">
              {overview!.meal_leftovers_count} — что съесть или приготовить
            </span>
          </button>
        </div>
      ) : null}

      <AIInsight2026
        text={insight}
        loading={loading}
        healthRelated={healthInsight}
      />

      <RecipeRail2026
        meals={meals}
        loading={loading}
        hasMenu={hasMenu}
        isNewUser={isNewUser}
        onCreateMenu={handleCreateMenu}
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
            {displayName ? `, ${displayName}` : ""}
          </h1>
        </div>
        <span className="shrink-0 rounded-pill border border-pa-border bg-pa-surface px-3 py-1.5 pa26-micro font-semibold text-sage-700 dark:text-sage-300">
          {scopeLabel}
        </span>
      </div>
    </header>
  );
}
