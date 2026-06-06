"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { MealOutcomeSheet2026 } from "@/components/dom-2026";
import { PlanAmHero2026 } from "@/components/home-2026/PlanAmHero2026";
import { PlanAmStatusRows2026 } from "@/components/home-2026/PlanAmStatusRows2026";
import { Button2026 } from "@/components/planam-2026/ui/Button2026";
import { BottomSheet2026 } from "@/components/planam-2026/ui/BottomSheet2026";
import { useTelegram } from "@/components/TelegramProvider";
import { EmptyState2026 } from "@/components/planam-2026/ui/EmptyState2026";
import {
  cacheKey,
  getCached,
  invalidate as invalidateCache,
  setCached,
} from "@/lib/cache/session-cache";
import { enrichTodayMeals } from "@/lib/home/home-2026-data";
import {
  formatPlanAmGreeting,
  resolvePlanAmHeroState,
} from "@/lib/home/planam-hero-2026";
import { fetchMenuOverview } from "@/lib/menu/overview-api";
import type { MenuOverview } from "@/lib/menu/overview-types";

type LoadState = "loading" | "ready" | "error";

export function Home2026() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { initData, user } = useTelegram();
  const { mode, loading: modeLoading } = useAppMode();

  const cacheK = cacheKey.menuOverview(mode);
  const primed = initData ? getCached<MenuOverview>(cacheK) : null;

  const [overview, setOverview] = useState<MenuOverview | null>(primed);
  const [loadState, setLoadState] = useState<LoadState>(() =>
    primed ? "ready" : "loading",
  );
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [mealOutcomeOpen, setMealOutcomeOpen] = useState(false);
  const [askOpen, setAskOpen] = useState(false);

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
  const heroState = useMemo(
    () => resolvePlanAmHeroState(overview, meals, hasMenu),
    [overview, meals, hasMenu],
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
  const greeting = useMemo(
    () => formatPlanAmGreeting(user?.first_name),
    [user?.first_name],
  );

  if (loadState === "error") {
    return (
      <div className="pb-2">
        <PlanAmGreeting greeting={greeting} />
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
      <PlanAmGreeting greeting={greeting} />

      <PlanAmHero2026 loading={loading} state={heroState} />

      <PlanAmStatusRows2026 overview={overview} loading={loading} />

      {!loading ? (
        <div className="flex gap-2 px-4 pt-2">
          <Button2026
            variant="secondary"
            size="default"
            className="flex-1 text-sm"
            onClick={() => router.push("/plan/today")}
          >
            Открыть меню
          </Button2026>
          <Button2026
            variant="secondary"
            size="default"
            className="flex-1 text-sm"
            onClick={() => router.push("/shopping")}
          >
            Список покупок
          </Button2026>
        </div>
      ) : null}

      {!loading ? (
        <div className="px-4 pt-3">
          <button
            type="button"
            onClick={() => setAskOpen(true)}
            className="flex w-full items-center justify-center gap-2 rounded-card border border-dashed border-pa-border bg-pa-surface/80 px-4 py-3 pa26-caption font-semibold text-sage-700 transition hover:bg-sage-50 dark:text-sage-300 dark:hover:bg-pa-elevated/40"
          >
            <span aria-hidden>✨</span>
            Спросить PlanAm
          </button>
        </div>
      ) : null}

      <BottomSheet2026
        open={askOpen}
        title="PlanAm"
        onClose={() => setAskOpen(false)}
      >
        <p className="pa26-body text-pa-muted">
          Скоро здесь появится помощник PlanAm.
        </p>
      </BottomSheet2026>

      <MealOutcomeSheet2026
        open={mealOutcomeOpen}
        onClose={() => setMealOutcomeOpen(false)}
        onSuccess={handleMealOutcomeSuccess}
      />
    </div>
  );
}

function PlanAmGreeting({ greeting }: { greeting: string }) {
  return (
    <header className="px-4 pb-1 pt-[max(0.5rem,env(safe-area-inset-top))]">
      <h1 className="pa26-page-title truncate">{greeting}</h1>
    </header>
  );
}
